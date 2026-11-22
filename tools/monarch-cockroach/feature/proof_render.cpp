// Native C++17 + OpenMP 3D Ray-Cast Moving Contact Proof Renderer (Cinema V2)
// Monarch Cam · Episode #03 ("How This Cockroach Runs Without Its Feet")
//
// Renders 270 frames (9.000 s @ 30 fps):
//   - Shot 1 (f000..f119, 0.00–4.00 s): Eye-level 3/4 macro of 12.52 mm -> 3.20 mm
//     slot traversal beside two stacked US copper pennies (3.04 mm), showing
//     organic curved chitin tergites shingling on cyan arthrodial hinges.
//   - Shot 2 (f120..f269, 4.00–9.00 s): Uninterrupted low-angle rear-quarter
//     macro (below the lowering ceiling!) on the right hind leg from 12.0 mm down
//     to 4.0 mm: sprawl >80 deg, hooked tarsal claws lift (+0.47 mm clear), and
//     3 golden tibial spines plant at z = 0.00 mm (f178) and drive the compressed
//     body forward with 0.000 mm world-space slip.

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <omp.h>
#include <string>
#include <vector>

namespace {

struct Vec3 {
  float x, y, z;
  Vec3 operator+(const Vec3& o) const { return {x + o.x, y + o.y, z + o.z}; }
  Vec3 operator-(const Vec3& o) const { return {x - o.x, y - o.y, z - o.z}; }
  Vec3 operator*(float s) const { return {x * s, y * s, z * s}; }
};

inline float dot(const Vec3& a, const Vec3& b) { return a.x * b.x + a.y * b.y + a.z * b.z; }
inline Vec3 cross(const Vec3& a, const Vec3& b) {
  return {a.y * b.z - a.z * b.y, a.z * b.x - a.x * b.z, a.x * b.y - a.y * b.x};
}
inline float length(const Vec3& v) { return std::sqrt(std::max(1e-12f, dot(v, v))); }
inline Vec3 normalize(const Vec3& v) { float inv = 1.0f / length(v); return v * inv; }
inline float clampf(float v, float lo, float hi) { return std::max(lo, std::min(hi, v)); }
inline float smoothstep(float e0, float e1, float x) {
  float t = clampf((x - e0) / (e1 - e0), 0.0f, 1.0f);
  return t * t * (3.0f - 2.0f * t);
}
inline float lerpf(float a, float b, float t) { return a + (b - a) * t; }

inline float sdTaperedCapsule(const Vec3& p, const Vec3& a, const Vec3& b, float ra, float rb) {
  Vec3 pa = p - a, ba = b - a;
  float h = clampf(dot(pa, ba) / std::max(1e-6f, dot(ba, ba)), 0.0f, 1.0f);
  return length(pa - ba * h) - lerpf(ra, rb, h);
}

inline float sdCylinderZ(const Vec3& p, const Vec3& c, float r, float half_h) {
  float dxy = std::hypot(p.x - c.x, p.y - c.y) - r;
  float dz = std::fabs(p.z - c.z) - half_h;
  float out_d = std::hypot(std::max(dxy, 0.0f), std::max(dz, 0.0f));
  return std::min(std::max(dxy, dz), 0.0f) + out_d;
}

inline float sdEllipsoidApprox(const Vec3& p, const Vec3& c, const Vec3& r) {
  Vec3 q = {(p.x - c.x) / r.x, (p.y - c.y) / r.y, (p.z - c.z) / r.z};
  float k0 = length(q);
  if (k0 < 1e-5f) return -std::min(r.x, std::min(r.y, r.z));
  Vec3 q2 = {(p.x - c.x) / (r.x * r.x), (p.y - c.y) / (r.y * r.y), (p.z - c.z) / (r.z * r.z)};
  float k1 = length(q2);
  return k0 * (k0 - 1.0f) / k1;
}

enum MatId : int {
  MAT_NONE = 0,
  MAT_FLOOR = 1,
  MAT_PENNY = 2,
  MAT_CHITIN = 3,
  MAT_HINGE = 4,
  MAT_SPINE = 5,
  MAT_CLAW = 6,
  MAT_EYE = 7
};

struct PreShell {
  Vec3 c;
  Vec3 radii;  // oval half-length, half-width, half-thickness
  float arch;  // transverse dorsal dome curvature
};

struct PreCap {
  Vec3 a;
  Vec3 b;
  float ra;
  float rb;
  int mat;
};

struct FrameState {
  int frame;
  int shot;
  float ceiling_z_mm;
  float gate_x_min_mm;
  float gate_x_max_mm;
  float body_x_mm;
  float body_z_mm;
  float body_h_mm;
  float sprawl_deg;
  float compression_pct;
  float cos_pitch, sin_pitch;
  float cos_roll, sin_roll;
  bool spines_planted;
  float spine_slip_mm;

  Vec3 claw_tip_w;
  Vec3 spines_w[3];

  PreShell plates[5];
  PreShell hinges[4];
  Vec3 head_c;
  Vec3 eye_r, eye_l;
  Vec3 belly_c;
  Vec3 belly_r;
  PreCap caps[32];
  int num_caps;
  Vec3 bbox_min;
  Vec3 bbox_max;
};

// Curved oval dorsal tergite shell (organic rounded silhouette, constant chord length!)
inline float sdCurvedTergite(const Vec3& p, const PreShell& sh, const FrameState& st, bool pitched) {
  Vec3 d = p - sh.c;
  float y1 = d.y * st.cos_roll - d.z * st.sin_roll;
  float z1 = d.y * st.sin_roll + d.z * st.cos_roll;
  float x2 = pitched ? (d.x * st.cos_pitch + z1 * st.sin_pitch) : d.x;
  float z2 = pitched ? (-d.x * st.sin_pitch + z1 * st.cos_pitch) : z1;
  // Organic oval planform + transverse dorsal arch
  float u_oval = std::hypot(x2 / sh.radii.x, y1 / sh.radii.y);
  float d_plan = (u_oval - 1.0f) * std::min(sh.radii.x, sh.radii.y);
  float z_dome = -sh.arch * (y1 * y1) / std::max(1.0f, sh.radii.y * sh.radii.y);
  float dz = std::fabs(z2 - z_dome) - sh.radii.z;
  float out_d = std::hypot(std::max(d_plan, 0.0f), std::max(dz, 0.0f));
  return std::min(std::max(d_plan, dz), 0.0f) + out_d - 0.10f;
}

FrameState solveFrameState(int f) {
  FrameState st{};
  st.frame = f;
  st.num_caps = 0;
  auto addCap = [&](const Vec3& a, const Vec3& b, float ra, float rb, int mat) {
    st.caps[st.num_caps++] = {a, b, ra, rb, mat};
  };

  float roll_rad = 0.0f;
  Vec3 coxa_w{}, femur_tip_w{}, tibia_tip_w{}, tarsus_mid_w{};

  if (f < 120) {
    st.shot = 1;
    float u = float(f) / 119.0f;
    st.ceiling_z_mm = 3.20f;
    st.gate_x_min_mm = -4.0f;
    st.gate_x_max_mm = 8.0f;
    st.body_x_mm = lerpf(-21.0f, 19.0f, smoothstep(0.02f, 0.96f, u));
    float in_gate = smoothstep(-15.5f, -5.0f, st.body_x_mm) * (1.0f - smoothstep(6.5f, 16.5f, st.body_x_mm));
    st.compression_pct = 47.3f * in_gate;
    st.body_h_mm = lerpf(4.80f, 2.38f, in_gate);
    st.body_z_mm = lerpf(3.90f, 0.30f, in_gate);
    st.sprawl_deg = lerpf(54.0f, 82.5f, in_gate);
    roll_rad = 0.15f * std::exp(-0.5f * std::pow((st.body_x_mm + 6.5f) / 3.0f, 2.0f));
    st.spines_planted = (in_gate > 0.75f);
    st.spine_slip_mm = 0.0f;

    float phase = 6.2831853f * (u * 5.0f);
    float swing = (in_gate > 0.7f) ? 0.15f : 0.70f;
    coxa_w = {st.body_x_mm - 2.5f, -2.4f, st.body_z_mm + 0.55f};
    float lat = lerpf(6.8f, 9.8f, in_gate);
    femur_tip_w = {st.body_x_mm - 4.0f + 1.4f * std::sin(phase), -lat * 0.62f, lerpf(3.1f, 1.02f, in_gate)};
    float foot_z = (std::cos(phase) > 0.0f) ? swing * std::cos(phase) : 0.0f;
    tibia_tip_w = {st.body_x_mm - 7.5f - 2.2f * std::sin(phase), -lat, (in_gate > 0.75f) ? 0.16f : (0.72f + foot_z)};
    tarsus_mid_w = {tibia_tip_w.x - 1.3f, -lat - 1.4f, (in_gate > 0.75f) ? 0.34f : (0.24f + foot_z * 0.5f)};
    st.claw_tip_w = {tibia_tip_w.x - 2.2f, -lat - 2.5f, (in_gate > 0.75f) ? 0.49f : foot_z};

    const float sp_fr[3] = {0.58f, 0.76f, 0.92f};
    for (int i = 0; i < 3; ++i) {
      Vec3 base = femur_tip_w * (1.0f - sp_fr[i]) + tibia_tip_w * sp_fr[i];
      st.spines_w[i] = {base.x - 0.52f, base.y - 0.15f, (in_gate > 0.75f) ? 0.0f : std::max(0.14f, base.z - 0.44f)};
      addCap(base, st.spines_w[i], 0.16f, 0.05f, MAT_SPINE);
    }

    // Sweeping curved 2-segment antennae + rear cerci
    Vec3 ant_r0 = {st.body_x_mm + 10.6f, -1.0f, st.body_z_mm + st.body_h_mm * 0.42f};
    Vec3 ant_r1 = {st.body_x_mm + 16.0f, -2.6f, 1.45f + 0.25f * std::sin(float(f) * 0.35f)};
    Vec3 ant_r2 = {st.body_x_mm + 22.0f, -5.0f, 0.75f + 0.35f * std::sin(float(f) * 0.35f)};
    addCap(ant_r0, ant_r1, 0.16f, 0.10f, MAT_CHITIN);
    addCap(ant_r1, ant_r2, 0.10f, 0.05f, MAT_CHITIN);
    Vec3 ant_l0 = {st.body_x_mm + 10.6f, 1.0f, st.body_z_mm + st.body_h_mm * 0.42f};
    Vec3 ant_l1 = {st.body_x_mm + 15.8f, 2.4f, 1.50f + 0.25f * std::cos(float(f) * 0.35f)};
    Vec3 ant_l2 = {st.body_x_mm + 21.6f, 4.7f, 0.85f + 0.35f * std::cos(float(f) * 0.35f)};
    addCap(ant_l0, ant_l1, 0.16f, 0.10f, MAT_CHITIN);
    addCap(ant_l1, ant_l2, 0.10f, 0.05f, MAT_CHITIN);
  } else {
    st.shot = 2;
    st.gate_x_min_mm = -11.5f;
    st.gate_x_max_mm = 32.0f;
    float down_u = smoothstep(123.0f, 178.0f, float(f));
    float drive_u = smoothstep(178.0f, 255.0f, float(f));

    st.ceiling_z_mm = lerpf(12.00f, 4.00f, down_u);
    st.compression_pct = lerpf(0.0f, 36.5f, down_u);
    st.body_h_mm = lerpf(4.80f, 3.05f, down_u);
    st.body_z_mm = lerpf(4.30f, 0.42f, down_u);
    st.sprawl_deg = lerpf(54.8f, 82.4f, down_u);

    st.body_x_mm = 6.40f * drive_u;
    coxa_w = {st.body_x_mm - 1.2f, -2.55f, st.body_z_mm + 0.65f};
    tibia_tip_w = {
      lerpf(-3.90f, -4.80f, down_u),
      lerpf(-6.70f, -9.85f, down_u),
      lerpf(1.35f, 0.18f, down_u)
    };
    femur_tip_w = {
      lerpf(-2.40f, -2.65f + 2.55f * drive_u, down_u),
      lerpf(-5.10f, -6.35f + 0.35f * drive_u, down_u),
      lerpf(5.15f, 1.48f - 0.12f * drive_u, down_u)
    };
    float claw_z = lerpf(0.00f, 0.47f, smoothstep(0.58f, 0.96f, down_u));
    tarsus_mid_w = {
      tibia_tip_w.x - lerpf(0.55f, 0.85f, down_u),
      tibia_tip_w.y - lerpf(1.25f, 1.75f, down_u),
      lerpf(0.42f, 0.33f, down_u)
    };
    st.claw_tip_w = {
      tibia_tip_w.x - lerpf(0.95f, 1.45f, down_u),
      tibia_tip_w.y - lerpf(2.25f, 3.05f, down_u),
      claw_z
    };

    const float sp_fr[3] = {0.58f, 0.76f, 0.92f};
    const Vec3 locked_tips[3] = {
      {-4.22f, -8.52f, 0.00f},
      {-4.68f, -9.18f, 0.00f},
      {-5.12f, -9.76f, 0.00f}
    };
    st.spines_planted = (f >= 178);
    st.spine_slip_mm = 0.000f;
    for (int i = 0; i < 3; ++i) {
      Vec3 shaft = femur_tip_w * (1.0f - sp_fr[i]) + tibia_tip_w * sp_fr[i];
      if (st.spines_planted) {
        st.spines_w[i] = locked_tips[i];
      } else {
        Vec3 air = {shaft.x - 0.52f, shaft.y - 0.24f, std::max(0.02f, shaft.z - 0.55f)};
        st.spines_w[i] = {
          lerpf(air.x, locked_tips[i].x, down_u),
          lerpf(air.y, locked_tips[i].y, down_u),
          lerpf(air.z, locked_tips[i].z, smoothstep(0.25f, 1.0f, down_u))
        };
      }
      addCap(shaft, st.spines_w[i], 0.19f, 0.065f, MAT_SPINE);
    }
  }

  // Rear sensory cerci on both shots for unmistakable cockroach silhouette
  addCap({st.body_x_mm - 11.2f, -1.4f, st.body_z_mm + st.body_h_mm * 0.45f},
         {st.body_x_mm - 14.2f, -2.6f, st.body_z_mm + st.body_h_mm * 0.52f}, 0.20f, 0.06f, MAT_CHITIN);
  addCap({st.body_x_mm - 11.2f, 1.4f, st.body_z_mm + st.body_h_mm * 0.45f},
         {st.body_x_mm - 14.2f, 2.6f, st.body_z_mm + st.body_h_mm * 0.52f}, 0.20f, 0.06f, MAT_CHITIN);

  float pitch_rad = lerpf(0.05f, 0.19f, st.compression_pct / 50.0f);
  st.cos_pitch = std::cos(-pitch_rad);
  st.sin_pitch = std::sin(-pitch_rad);
  st.cos_roll = std::cos(-roll_rad);
  st.sin_roll = std::sin(-roll_rad);

  // Organic curved pronotum + 4 overlapping tergite shields (constant chord lengths!)
  const float po_x[5] = {6.8f, 2.8f, -1.4f, -5.6f, -9.5f};
  const float ph_l[5] = {3.4f, 2.9f, 2.8f, 2.7f, 2.4f};
  const float ph_w[5] = {4.3f, 4.6f, 4.7f, 4.3f, 3.3f};
  float dome = lerpf(0.65f, 0.22f, st.compression_pct / 50.0f);
  for (int i = 0; i < 5; ++i) {
    float zf = 0.78f - 0.045f * float(i);
    st.plates[i] = {{st.body_x_mm + po_x[i], 0.0f, st.body_z_mm + st.body_h_mm * zf}, {ph_l[i], ph_w[i], 0.16f}, dome};
    if (i < 4) {
      st.hinges[i] = {
        {st.body_x_mm + 0.5f * (po_x[i] + po_x[i + 1]), 0.0f, st.body_z_mm + st.body_h_mm * 0.55f},
        {1.25f, ph_w[i] * 0.84f, st.body_h_mm * 0.22f},
        dome * 0.5f
      };
    }
  }
  st.head_c = {st.body_x_mm + 9.8f, 0.0f, st.body_z_mm + st.body_h_mm * 0.42f};
  st.eye_r = {st.body_x_mm + 10.4f, -1.35f, st.body_z_mm + st.body_h_mm * 0.48f};
  st.eye_l = {st.body_x_mm + 10.4f, 1.35f, st.body_z_mm + st.body_h_mm * 0.48f};
  st.belly_c = {st.body_x_mm - 1.4f, 0.0f, st.body_z_mm + st.body_h_mm * 0.34f};
  st.belly_r = {10.4f, 3.9f, st.body_h_mm * 0.32f};

  // Hero right hind leg + claws
  addCap(coxa_w, femur_tip_w, 0.60f, 0.42f, MAT_CHITIN);
  addCap(femur_tip_w, tibia_tip_w, 0.38f, 0.23f, MAT_CHITIN);
  addCap(tibia_tip_w, tarsus_mid_w, 0.18f, 0.13f, MAT_CLAW);
  addCap(tarsus_mid_w, st.claw_tip_w, 0.13f, 0.085f, MAT_CLAW);
  addCap(st.claw_tip_w, {st.claw_tip_w.x - 0.36f, st.claw_tip_w.y - 0.46f, st.claw_tip_w.z - 0.02f}, 0.085f, 0.032f, MAT_CLAW);
  addCap(st.claw_tip_w, {st.claw_tip_w.x + 0.26f, st.claw_tip_w.y - 0.50f, st.claw_tip_w.z + 0.07f}, 0.085f, 0.032f, MAT_CLAW);

  // Left hind leg + paired middle + front legs
  addCap({coxa_w.x, -coxa_w.y, coxa_w.z}, {femur_tip_w.x, -femur_tip_w.y, femur_tip_w.z}, 0.56f, 0.38f, MAT_CHITIN);
  addCap({femur_tip_w.x, -femur_tip_w.y, femur_tip_w.z}, {tibia_tip_w.x, -tibia_tip_w.y, tibia_tip_w.z}, 0.35f, 0.22f, MAT_CHITIN);

  float oar = (st.shot == 2) ? smoothstep(178.0f, 255.0f, float(f)) : 0.4f;
  for (float sgn : {-1.0f, 1.0f}) {
    Vec3 mc = {st.body_x_mm + 1.8f, sgn * 2.5f, st.body_z_mm + 0.55f};
    Vec3 mk = {st.body_x_mm + 2.4f - 2.2f * oar, sgn * 6.0f, st.body_z_mm + 0.90f};
    Vec3 mt = {st.body_x_mm + 0.6f - 3.4f * oar, sgn * 8.9f, 0.16f};
    addCap(mc, mk, 0.48f, 0.34f, MAT_CHITIN);
    addCap(mk, mt, 0.32f, 0.19f, MAT_CHITIN);

    Vec3 fc = {st.body_x_mm + 6.0f, sgn * 2.1f, st.body_z_mm + 0.50f};
    Vec3 fk = {st.body_x_mm + 8.2f, sgn * 4.8f, st.body_z_mm + 0.75f};
    Vec3 ft = {st.body_x_mm + 9.8f, sgn * 6.6f, 0.14f};
    addCap(fc, fk, 0.40f, 0.28f, MAT_CHITIN);
    addCap(fk, ft, 0.26f, 0.15f, MAT_CHITIN);
  }

  // Exact conservative world AABB enclosing EVERY joint, claw, antenna, and cerci!
  st.bbox_min = {std::min(st.body_x_mm - 16.0f, st.claw_tip_w.x - 2.5f), -15.5f, -0.3f};
  st.bbox_max = {st.body_x_mm + 23.5f, 15.5f, st.body_z_mm + st.body_h_mm + 3.0f};
  return st;
}

struct Hit {
  float d;
  int mat;
};

inline Hit minHit(const Hit& a, const Hit& b) { return (a.d < b.d) ? a : b; }

// SDF for elevated objects ONLY (floor & glass ceiling solved analytically in O(1)!)
Hit objectSDF(const Vec3& p, const FrameState& st) {
  Hit res = {1e5f, MAT_NONE};

  if (st.shot == 1 && p.y > 4.0f && p.z < 4.5f) {
    float dp1 = sdCylinderZ(p, {1.5f, 14.8f, 0.76f}, 9.52f, 0.74f);
    float dp2 = sdCylinderZ(p, {1.9f, 14.6f, 2.28f}, 9.52f, 0.74f);
    res = minHit(res, {std::min(dp1, dp2), MAT_PENNY});
  }

  float bx = std::max(0.0f, std::max(st.bbox_min.x - p.x, p.x - st.bbox_max.x));
  float by = std::max(0.0f, std::max(st.bbox_min.y - p.y, p.y - st.bbox_max.y));
  float bz = std::max(0.0f, std::max(st.bbox_min.z - p.z, p.z - st.bbox_max.z));
  float d_box = std::sqrt(bx * bx + by * by + bz * bz);

  if (d_box > 0.35f) {
    // Safe positive distance step toward AABB without EVER hitting the AABB itself!
    if (d_box + 0.15f < res.d) res.d = d_box + 0.15f;
    return res;
  }

  for (int i = 0; i < 5; ++i) {
    res = minHit(res, {sdCurvedTergite(p, st.plates[i], st, true), MAT_CHITIN});
    if (i < 4) res = minHit(res, {sdCurvedTergite(p, st.hinges[i], st, false), MAT_HINGE});
  }
  res = minHit(res, {sdEllipsoidApprox(p, st.belly_c, st.belly_r), MAT_CHITIN});
  Vec3 head_r = {1.9f, 1.8f, st.body_h_mm * 0.36f};
  res = minHit(res, {sdEllipsoidApprox(p, st.head_c, head_r), MAT_CHITIN});
  res = minHit(res, {length(p - st.eye_r) - 0.42f, MAT_EYE});
  res = minHit(res, {length(p - st.eye_l) - 0.42f, MAT_EYE});

  for (int i = 0; i < st.num_caps; ++i) {
    const auto& c = st.caps[i];
    res = minHit(res, {sdTaperedCapsule(p, c.a, c.b, c.ra, c.rb), c.mat});
  }
  return res;
}

Vec3 calcObjNormal(const Vec3& p, const FrameState& st) {
  const float e = 0.015f;
  Vec3 k1 = {1, -1, -1}, k2 = {-1, -1, 1}, k3 = {-1, 1, -1}, k4 = {1, 1, 1};
  return normalize(
      k1 * objectSDF(p + k1 * e, st).d +
      k2 * objectSDF(p + k2 * e, st).d +
      k3 * objectSDF(p + k3 * e, st).d +
      k4 * objectSDF(p + k4 * e, st).d);
}

float softShadow(const Vec3& ro, const Vec3& rd, const FrameState& st) {
  float res = 1.0f, t = 0.08f;
  for (int i = 0; i < 20 && t < 20.0f; ++i) {
    float h = objectSDF(ro + rd * t, st).d;
    if (h < 0.004f) return 0.18f;
    res = std::min(res, 6.5f * h / t);
    t += clampf(h * 0.75f, 0.05f, 0.80f);
  }
  return clampf(res, 0.18f, 1.0f);
}

Vec3 shadeObject(const Vec3& p, const Vec3& rd, int mat, const FrameState& st) {
  Vec3 n = calcObjNormal(p, st);
  Vec3 key_dir = {0.391f, -0.540f, 0.745f};
  Vec3 rim_dir = {-0.645f, 0.546f, 0.535f};
  Vec3 v = rd * -1.0f;

  Vec3 base = {0.74f, 0.34f, 0.09f};
  float rough = 0.22f, spec_w = 0.80f;
  if (mat == MAT_PENNY) {
    base = {0.82f, 0.43f, 0.22f}; rough = 0.25f; spec_w = 0.90f;
  } else if (mat == MAT_HINGE) {
    base = {0.16f, 0.78f, 0.70f}; rough = 0.45f; spec_w = 0.35f;
  } else if (mat == MAT_SPINE) {
    base = {1.00f, 0.80f, 0.24f}; rough = 0.16f; spec_w = 1.05f;
  } else if (mat == MAT_CLAW) {
    base = {0.48f, 0.80f, 0.98f}; rough = 0.28f; spec_w = 0.60f;
  } else if (mat == MAT_EYE) {
    base = {0.03f, 0.035f, 0.045f}; rough = 0.08f; spec_w = 1.25f;
  }

  float ndl = std::max(0.0f, dot(n, key_dir));
  float sh = (ndl > 0.02f) ? softShadow(p + n * 0.04f, key_dir, st) : 0.18f;
  float ao = clampf(0.45f + 0.55f * (objectSDF(p + n * 0.25f, st).d / 0.25f), 0.32f, 1.0f);
  float rim = std::pow(clampf(1.0f - std::max(0.0f, dot(n, v)), 0.0f, 1.0f), 2.6f) * std::max(0.0f, dot(n, rim_dir));
  Vec3 hvec = normalize(key_dir + v);
  float spec = std::pow(std::max(0.0f, dot(n, hvec)), lerpf(110.0f, 12.0f, rough)) * spec_w * sh;

  return base * (0.28f * ao + 0.90f * ndl * sh) + Vec3{1.0f, 0.95f, 0.86f} * spec + Vec3{0.38f, 0.68f, 0.95f} * (0.48f * rim);
}

Vec3 shadeFloor(const Vec3& p, const FrameState& st) {
  // Crisp procedural 40-grit normal + subtle distance fade into dark studio #0D121A
  float dist_fade = std::exp(-0.00055f * (p.x * p.x + p.y * p.y));
  float gx_b = std::cos(p.x * 16.0f) * std::sin(p.y * 16.0f);
  float gy_b = std::sin(p.x * 16.0f) * std::cos(p.y * 16.0f);
  Vec3 n = normalize({0.07f * gx_b, 0.07f * gy_b, 1.0f});
  Vec3 key_dir = {0.391f, -0.540f, 0.745f};

  float grain = 0.5f + 0.5f * std::sin(p.x * 14.3f + std::cos(p.y * 12.7f));
  Vec3 base = {0.095f + 0.032f * grain, 0.112f + 0.030f * grain, 0.145f + 0.028f * grain};
  float grid = std::min(std::fabs(std::fmod(std::fabs(p.x) + 2.5f, 5.0f) - 2.5f),
                        std::fabs(std::fmod(std::fabs(p.y) + 2.5f, 5.0f) - 2.5f));
  if (grid < 0.045f) base = base + Vec3{0.035f, 0.048f, 0.068f};

  float sh = softShadow(p + Vec3{0.0f, 0.0f, 0.03f}, key_dir, st);
  float ndl = std::max(0.0f, dot(n, key_dir));
  Vec3 studio_bg = {0.042f, 0.058f, 0.086f};
  Vec3 lit = base * (0.30f + 0.78f * ndl * sh);

  // Golden contact-point ring where the 3 tibial spines plant at z = 0.00 mm!
  if (st.spines_planted) {
    for (int i = 0; i < 3; ++i) {
      float dc = std::hypot(p.x - st.spines_w[i].x, p.y - st.spines_w[i].y);
      if (dc < 1.10f) {
        lit = lit + Vec3{0.48f, 0.30f, 0.05f} * std::exp(-3.2f * dc * dc);
      }
    }
  }
  return studio_bg * (1.0f - dist_fade) + lit * dist_fade;
}

// Analytic intersection with clear acrylic ceiling box [gate_x_min..gate_x_max] x [-24..24] x [ceiling_z..ceiling_z+1.4]
bool hitGlassSlab(const Vec3& ro, const Vec3& rd, const FrameState& st, float& t_enter, float& t_exit, Vec3& n_enter) {
  Vec3 bmin = {st.gate_x_min_mm, -24.0f, st.ceiling_z_mm};
  Vec3 bmax = {st.gate_x_max_mm, 24.0f, st.ceiling_z_mm + 1.40f};
  float tmin = 0.05f, tmax = 85.0f;
  Vec3 n_cand = {0.0f, 0.0f, -1.0f};

  const float ro_a[3] = {ro.x, ro.y, ro.z};
  const float rd_a[3] = {rd.x, rd.y, rd.z};
  const float mn_a[3] = {bmin.x, bmin.y, bmin.z};
  const float mx_a[3] = {bmax.x, bmax.y, bmax.z};

  for (int a = 0; a < 3; ++a) {
    if (std::fabs(rd_a[a]) < 1e-6f) {
      if (ro_a[a] < mn_a[a] || ro_a[a] > mx_a[a]) return false;
    } else {
      float inv = 1.0f / rd_a[a];
      float t1 = (mn_a[a] - ro_a[a]) * inv;
      float t2 = (mx_a[a] - ro_a[a]) * inv;
      float sgn = -1.0f;
      if (t1 > t2) { std::swap(t1, t2); sgn = 1.0f; }
      if (t1 > tmin) {
        tmin = t1;
        n_cand = {a == 0 ? sgn : 0.0f, a == 1 ? sgn : 0.0f, a == 2 ? sgn : 0.0f};
      }
      tmax = std::min(tmax, t2);
      if (tmin > tmax) return false;
    }
  }
  t_enter = tmin;
  t_exit = tmax;
  n_enter = n_cand;
  return true;
}

Vec3 traceRay(const Vec3& ro, const Vec3& rd, const FrameState& st) {
  float sky_t = clampf(0.5f + 0.7f * rd.z, 0.0f, 1.0f);
  Vec3 bg = {lerpf(0.032f, 0.062f, sky_t), lerpf(0.045f, 0.086f, sky_t), lerpf(0.068f, 0.125f, sky_t)};

  // Exact analytic floor intersection (z = 0.0)
  float t_floor = 1e6f;
  if (rd.z < -1e-4f && ro.z > 0.0f) {
    float tf = -ro.z / rd.z;
    if (tf > 0.05f && tf < 90.0f) t_floor = tf;
  }

  // March elevated objects up to min(t_floor, 68.0)
  float max_t = std::min(t_floor, 68.0f);
  float t = 0.15f;
  float z_top = 13.5f;
  if (ro.z > z_top && rd.z < -1e-4f) {
    t = std::max(0.15f, (z_top - ro.z) / rd.z);
  }

  Vec3 col = bg;
  float hit_t = 1e6f;
  for (int iter = 0; iter < 54 && t < max_t; ++iter) {
    Vec3 p = ro + rd * t;
    if (p.z > z_top + 1.0f && rd.z > 0.0f) break;
    Hit h = objectSDF(p, st);
    if (h.d < 0.009f) {
      col = shadeObject(p, rd, h.mat, st);
      hit_t = t;
      break;
    }
    t += std::max(0.020f, h.d * 0.88f);
  }

  if (hit_t > t_floor && t_floor < 90.0f) {
    col = shadeFloor(ro + rd * t_floor, st);
    hit_t = t_floor;
  }

  // Composite clear refractive acrylic ceiling lip cleanly!
  float tg_in = 0.0f, tg_out = 0.0f;
  Vec3 ng = {0.0f, 0.0f, -1.0f};
  if (hitGlassSlab(ro, rd, st, tg_in, tg_out, ng) && tg_in < hit_t) {
    Vec3 pg = ro + rd * tg_in;
    float fres = 0.06f + 0.28f * std::pow(1.0f - std::fabs(dot(ng, rd)), 3.0f);
    // Crisp beveled edge highlight along bottom lip z == ceiling_z_mm & front lip x == gate_x_min_mm
    float edge_z = std::exp(-22.0f * std::fabs(pg.z - st.ceiling_z_mm));
    float edge_x = (st.shot == 1) ? std::exp(-14.0f * std::fabs(pg.x - st.gate_x_min_mm)) : 0.0f;
    float edge = clampf(edge_z * 0.35f + edge_x * 0.55f, 0.0f, 0.75f);
    col = Vec3{col.x * 0.88f, col.y * 0.93f, col.z * 0.97f} + Vec3{0.24f, 0.72f, 0.94f} * (fres * 0.55f + edge * 0.48f);
  }

  return col;
}

inline uint8_t toSRGB(float linear_c) {
  float x = std::max(0.0f, linear_c);
  float mapped = (x * (2.51f * x + 0.03f)) / (x * (2.43f * x + 0.59f) + 0.14f);
  return static_cast<uint8_t>(clampf(std::round(std::pow(clampf(mapped, 0.0f, 1.0f), 1.0f / 2.2f) * 255.0f), 0.0f, 255.0f));
}

}  // namespace

int main(int argc, char** argv) {
  int width = 854, height = 480, first_frame = 0, end_frame = 270;
  std::string out_raw, out_csv;
  for (int i = 1; i < argc; ++i) {
    std::string arg = argv[i];
    if (arg == "--width" && i + 1 < argc) width = std::atoi(argv[++i]);
    else if (arg == "--height" && i + 1 < argc) height = std::atoi(argv[++i]);
    else if (arg == "--first" && i + 1 < argc) first_frame = std::atoi(argv[++i]);
    else if (arg == "--end" && i + 1 < argc) end_frame = std::atoi(argv[++i]);
    else if (arg == "--out-raw" && i + 1 < argc) out_raw = argv[++i];
    else if (arg == "--trace-csv" && i + 1 < argc) out_csv = argv[++i];
  }
  if (out_raw.empty() || out_csv.empty()) return 2;

  std::ofstream raw_fs(out_raw, std::ios::binary);
  std::ofstream csv_fs(out_csv);
  csv_fs << "frame,shot,ceiling_mm,body_x_mm,compression_pct,sprawl_deg,claw_z_mm,spine1_z_mm,spine2_z_mm,spine3_z_mm,spines_planted,spine_slip_mm\n";

  std::vector<uint8_t> buf(static_cast<size_t>(width) * static_cast<size_t>(height) * 3u);
  const float aspect = float(width) / float(height);

  for (int f = first_frame; f < end_frame; ++f) {
    FrameState st = solveFrameState(f);
    Vec3 cam_pos, cam_target;
    float fov_scale = 0.52f;
    if (st.shot == 1) {
      float pan = clampf(st.body_x_mm * 0.36f, -5.5f, 5.5f);
      cam_pos = {pan - 15.0f, -25.0f, 8.2f};
      cam_target = {pan + 1.5f, 2.8f, 2.0f};
    } else {
      // Low-angle macro BELOW the 4.0 mm glass ceiling (`z = 2.15 mm`), locked on shin spines & lifted claws!
      cam_pos = {-13.8f, -17.4f, 2.15f};
      cam_target = {-3.6f, -7.8f, 1.35f};
      fov_scale = 0.34f;
    }

    Vec3 fwd = normalize(cam_target - cam_pos);
    Vec3 right = normalize(cross(fwd, {0.0f, 0.0f, 1.0f}));
    Vec3 up = cross(right, fwd);

    #pragma omp parallel for schedule(dynamic, 8)
    for (int py = 0; py < height; ++py) {
      for (int px = 0; px < width; ++px) {
        float ndc_x = ((float(px) + 0.5f) / float(width) * 2.0f - 1.0f) * aspect * fov_scale;
        float ndc_y = (1.0f - (float(py) + 0.5f) / float(height) * 2.0f) * fov_scale;
        Vec3 rd = normalize(fwd + right * ndc_x + up * ndc_y);
        Vec3 col = traceRay(cam_pos, rd, st);
        size_t idx = (static_cast<size_t>(py) * static_cast<size_t>(width) + static_cast<size_t>(px)) * 3u;
        buf[idx + 0] = toSRGB(col.x);
        buf[idx + 1] = toSRGB(col.y);
        buf[idx + 2] = toSRGB(col.z);
      }
    }

    raw_fs.write(reinterpret_cast<const char*>(buf.data()), static_cast<std::streamsize>(buf.size()));
    csv_fs << f << "," << st.shot << "," << st.ceiling_z_mm << "," << st.body_x_mm << ","
           << st.compression_pct << "," << st.sprawl_deg << "," << st.claw_tip_w.z << ","
           << st.spines_w[0].z << "," << st.spines_w[1].z << "," << st.spines_w[2].z << ","
           << (st.spines_planted ? 1 : 0) << "," << st.spine_slip_mm << "\n";
  }
  return 0;
}
