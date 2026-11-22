// Monarch Cam Episode #03 — Full 16:9 Feature Film Analytic 3D Renderer (C++17 + OpenMP)
// Renders all 7 voice-locked chapters (10,461 frames @ 30.000 fps = 348.700 s) using
// exact closed-form ray-ellipsoid, ray-capsule, ray-cylinder, and ray-slab intersections
// grounded in Jayaram & Full, PNAS 2016 (PMC4776529). Zero iterative marching artifacts.

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <iostream>
#include <string>
#include <vector>

#ifdef _OPENMP
#include <omp.h>
#endif

namespace {

constexpr float kPi = 3.14159265358979323846f;

struct Vec3 {
  float x, y, z;
  Vec3(float x_ = 0.f, float y_ = 0.f, float z_ = 0.f) : x(x_), y(y_), z(z_) {}
  Vec3 operator+(const Vec3& o) const { return {x + o.x, y + o.y, z + o.z}; }
  Vec3 operator-(const Vec3& o) const { return {x - o.x, y - o.y, z - o.z}; }
  Vec3 operator*(float s) const { return {x * s, y * s, z * s}; }
};

inline Vec3 mul3(const Vec3& a, const Vec3& b) { return {a.x * b.x, a.y * b.y, a.z * b.z}; }
inline float dot(const Vec3& a, const Vec3& b) { return a.x * b.x + a.y * b.y + a.z * b.z; }
inline Vec3 cross(const Vec3& a, const Vec3& b) {
  return {a.y * b.z - a.z * b.y, a.z * b.x - a.x * b.z, a.x * b.y - a.y * b.x};
}
inline float len(const Vec3& v) { return std::sqrt(std::max(1e-12f, dot(v, v))); }
inline Vec3 norm(const Vec3& v) { return v * (1.0f / len(v)); }
inline float clampf(float v, float lo, float hi) { return std::max(lo, std::min(hi, v)); }
inline float smoothstep(float e0, float e1, float x) {
  float t = clampf((x - e0) / (e1 - e0), 0.0f, 1.0f);
  return t * t * (3.0f - 2.0f * t);
}
inline float lerpf(float a, float b, float t) { return a + (b - a) * t; }
inline Vec3 lerp3(const Vec3& a, const Vec3& b, float t) { return a + (b - a) * t; }

enum MatId : int {
  MAT_SKY = 0,
  MAT_FLOOR = 1,
  MAT_CHITIN = 2,
  MAT_HINGE = 3,
  MAT_SPINE = 4,
  MAT_CLAW = 5,
  MAT_PENNY = 6,
  MAT_EYE = 7,
  MAT_DOOR_WOOD = 8,
  MAT_LOAD_CELL = 9,
  MAT_BOULDER_GRIT = 10
};

struct Ellipsoid {
  Vec3 c;
  Vec3 ax_x;  // rotated unit X
  Vec3 ax_y;  // rotated unit Y
  Vec3 ax_z;  // rotated unit Z
  Vec3 inv_r;
  float bound_r;
  int mat;
};

struct Capsule {
  Vec3 a;
  Vec3 ba;
  float baba;
  float r;
  Vec3 mid;
  float bound_r;
  int mat;
};

struct CylinderZ {
  Vec3 c;     // center (x, y, z_mid)
  float r;
  float hz;   // half-height in Z
  int mat;
};

struct BoxSlab {
  Vec3 bmin;
  Vec3 bmax;
  int mat;
  bool translucent;
};

struct SceneState {
  int frame = 0;
  int chapter = 1;
  int subscene = 0;
  float t_sec = 0.0f;

  // Physics telemetry for HUD & trace verification
  float ceiling_mm = 12.52f;
  float body_top_mm = 11.4f;
  float compression_pct = 0.0f;
  float speed_cm_s = 58.05f;
  float claw_z_mm = 0.0f;
  float load_bw_mult = 0.0f;
  int floor_grit_mode = 1;  // 0=slick, 1=medium 40-grit, 2=coarse 20-grit boulders, 3=kitchen tile
  int spines_planted = 0;
  float light_switch_on = 1.0f;
  float fade_gain = 1.0f;

  Vec3 roach_center;
  float roach_bound_r = 28.0f;

  Ellipsoid ells[36];
  int num_ells = 0;

  Capsule caps[44];
  int num_caps = 0;

  CylinderZ cyls[6];
  int num_cyls = 0;

  BoxSlab slabs[4];
  int num_slabs = 0;

  Vec3 spine_glow_pts[6];
  int num_glow_pts = 0;

  Vec3 cam_pos;
  Vec3 cam_target;
  float fov_deg = 34.0f;

  void addEll(const Vec3& c, const Vec3& radii, float pitch_rad, float roll_rad, float yaw_rad, int mat) {
    if (num_ells >= 36) return;
    float cy = std::cos(yaw_rad), sy = std::sin(yaw_rad);
    float cp = std::cos(pitch_rad), sp = std::sin(pitch_rad);
    float cr = std::cos(roll_rad), sr = std::sin(roll_rad);
    // Intrinsic Z-Y-X basis
    Vec3 ux = {cy * cp, sy * cp, -sp};
    Vec3 uy = {cy * sp * sr - sy * cr, sy * sp * sr + cy * cr, cp * sr};
    Vec3 uz = {cy * sp * cr + sy * sr, sy * sp * cr - cy * sr, cp * cr};
    Ellipsoid& e = ells[num_ells++];
    e.c = c;
    e.ax_x = ux;
    e.ax_y = uy;
    e.ax_z = uz;
    e.inv_r = {1.0f / radii.x, 1.0f / radii.y, 1.0f / radii.z};
    e.bound_r = std::max({radii.x, radii.y, radii.z}) + 0.05f;
    e.mat = mat;
  }

  void addCap(const Vec3& a, const Vec3& b, float r, int mat) {
    if (num_caps >= 44) return;
    Capsule& c = caps[num_caps++];
    c.a = a;
    c.ba = b - a;
    c.baba = std::max(1e-7f, dot(c.ba, c.ba));
    c.r = r;
    c.mid = (a + b) * 0.5f;
    c.bound_r = 0.5f * std::sqrt(c.baba) + r + 0.05f;
    c.mat = mat;
  }

  void addCyl(const Vec3& c, float r, float hz, int mat) {
    if (num_cyls >= 6) return;
    cyls[num_cyls++] = {c, r, hz, mat};
  }

  void addSlab(const Vec3& bmin, const Vec3& bmax, int mat, bool translucent) {
    if (num_slabs >= 4) return;
    slabs[num_slabs++] = {bmin, bmax, mat, translucent};
  }
};

// Exact closed-form Ray-Ellipsoid intersection
inline bool hitEllipsoid(const Vec3& ro, const Vec3& rd, const Ellipsoid& e, float t_max, float& out_t, Vec3& out_n) {
  Vec3 oc = ro - e.c;
  float bproj = dot(oc, rd);
  float c_sph = dot(oc, oc) - e.bound_r * e.bound_r;
  if (c_sph > 0.0f && bproj > 0.0f) return false;
  if (bproj * bproj - c_sph < 0.0f) return false;

  Vec3 lo = {dot(oc, e.ax_x) * e.inv_r.x, dot(oc, e.ax_y) * e.inv_r.y, dot(oc, e.ax_z) * e.inv_r.z};
  Vec3 ld = {dot(rd, e.ax_x) * e.inv_r.x, dot(rd, e.ax_y) * e.inv_r.y, dot(rd, e.ax_z) * e.inv_r.z};
  float a = dot(ld, ld);
  float b = dot(lo, ld);
  float c = dot(lo, lo) - 1.0f;
  float h = b * b - a * c;
  if (h < 0.0f) return false;
  h = std::sqrt(h);
  float t = (-b - h) / a;
  if (t < 0.005f) t = (-b + h) / a;
  if (t < 0.005f || t >= t_max) return false;
  out_t = t;
  Vec3 lp = lo + ld * t;
  Vec3 gn = e.ax_x * (lp.x * e.inv_r.x) + e.ax_y * (lp.y * e.inv_r.y) + e.ax_z * (lp.z * e.inv_r.z);
  out_n = norm(gn);
  return true;
}

// Exact closed-form Ray-Capsule intersection (Inigo Quilez analytical formulation)
inline bool hitCapsule(const Vec3& ro, const Vec3& rd, const Capsule& cap, float t_max, float& out_t, Vec3& out_n) {
  Vec3 oc_m = ro - cap.mid;
  float bm = dot(oc_m, rd);
  float cm = dot(oc_m, oc_m) - cap.bound_r * cap.bound_r;
  if (cm > 0.0f && bm > 0.0f) return false;
  if (bm * bm - cm < 0.0f) return false;

  Vec3 oa = ro - cap.a;
  float bard = dot(cap.ba, rd);
  float baoa = dot(cap.ba, oa);
  float rdoa = dot(rd, oa);
  float oaoa = dot(oa, oa);
  float a = cap.baba - bard * bard;
  float b = cap.baba * rdoa - baoa * bard;
  float c = cap.baba * oaoa - baoa * baoa - cap.r * cap.r * cap.baba;
  float h = b * b - a * c;
  if (h >= 0.0f && std::fabs(a) > 1e-7f) {
    float t = (-b - std::sqrt(h)) / a;
    float y = baoa + t * bard;
    if (y > 0.0f && y < cap.baba) {
      if (t > 0.005f && t < t_max) {
        out_t = t;
        Vec3 pa = oa + rd * t;
        out_n = (pa - cap.ba * (y / cap.baba)) * (1.0f / cap.r);
        return true;
      }
    }
    // Check spherical endcap closest to ray entry
    Vec3 oc = (y <= 0.0f) ? oa : (ro - (cap.a + cap.ba));
    b = dot(rd, oc);
    c = dot(oc, oc) - cap.r * cap.r;
    float h2 = b * b - c;
    if (h2 >= 0.0f) {
      float t2 = -b - std::sqrt(h2);
      if (t2 > 0.005f && t2 < t_max) {
        out_t = t2;
        out_n = (oc + rd * t2) * (1.0f / cap.r);
        return true;
      }
    }
  }
  return false;
}

// Exact closed-form Z-aligned Capped Cylinder intersection (US pennies, coarse grains, load plate)
inline bool hitCylinderZ(const Vec3& ro, const Vec3& rd, const CylinderZ& cy, float t_max, float& out_t, Vec3& out_n) {
  float ox = ro.x - cy.c.x, oy = ro.y - cy.c.y, oz = ro.z - cy.c.z;
  float best_t = t_max;
  Vec3 best_n;
  bool hit = false;

  // Endcaps z = ±hz
  if (std::fabs(rd.z) > 1e-6f) {
    for (int sgn : {-1, 1}) {
      float t = (sgn * cy.hz - oz) / rd.z;
      if (t > 0.005f && t < best_t) {
        float px = ox + rd.x * t, py = oy + rd.y * t;
        if (px * px + py * py <= cy.r * cy.r) {
          best_t = t;
          best_n = {0.0f, 0.0f, static_cast<float>(sgn)};
          hit = true;
        }
      }
    }
  }
  // Curved side wall
  float a = rd.x * rd.x + rd.y * rd.y;
  if (a > 1e-7f) {
    float b = ox * rd.x + oy * rd.y;
    float c = ox * ox + oy * oy - cy.r * cy.r;
    float h = b * b - a * c;
    if (h >= 0.0f) {
      float t = (-b - std::sqrt(h)) / a;
      if (t > 0.005f && t < best_t) {
        float pz = oz + rd.z * t;
        if (std::fabs(pz) <= cy.hz) {
          best_t = t;
          best_n = norm({ox + rd.x * t, oy + rd.y * t, 0.0f});
          hit = true;
        }
      }
    }
  }
  if (hit) {
    out_t = best_t;
    out_n = best_n;
  }
  return hit;
}

// Exact AABB slab intersection
inline bool hitBox(const Vec3& ro, const Vec3& rd, const Vec3& bmin, const Vec3& bmax, float& t_near, float& t_far, Vec3& n_near) {
  t_near = -1e9f;
  t_far = 1e9f;
  Vec3 n_candidate = {0.0f, 0.0f, 1.0f};
  const float ro_a[3] = {ro.x, ro.y, ro.z};
  const float rd_a[3] = {rd.x, rd.y, rd.z};
  const float mn_a[3] = {bmin.x, bmin.y, bmin.z};
  const float mx_a[3] = {bmax.x, bmax.y, bmax.z};
  for (int i = 0; i < 3; ++i) {
    if (std::fabs(rd_a[i]) < 1e-7f) {
      if (ro_a[i] < mn_a[i] || ro_a[i] > mx_a[i]) return false;
    } else {
      float inv = 1.0f / rd_a[i];
      float t1 = (mn_a[i] - ro_a[i]) * inv;
      float t2 = (mx_a[i] - ro_a[i]) * inv;
      float sgn = -1.0f;
      if (t1 > t2) {
        std::swap(t1, t2);
        sgn = 1.0f;
      }
      if (t1 > t_near) {
        t_near = t1;
        n_candidate = {i == 0 ? sgn : 0.f, i == 1 ? sgn : 0.f, i == 2 ? sgn : 0.f};
      }
      t_far = std::min(t_far, t2);
      if (t_near > t_far) return false;
    }
  }
  n_near = n_candidate;
  return t_far > 0.005f;
}

// Assemble full 31.10 mm articulated cockroach at any compression/gait state
void populateCockroach(
    SceneState& st,
    float body_x_mm,
    float body_y_mm,
    float body_top_mm,
    float gait_phase,
    bool tripod_mode,
    bool oar_midlegs,
    bool rear_spine_lock,
    float locked_spine_world_x,
    float pronotum_roll_rad,
    float head_pitch_extra_rad) {
  st.roach_center = {body_x_mm - 11.5f, body_y_mm, body_top_mm * 0.48f};
  st.roach_bound_r = 21.5f;

  const float squeeze = clampf((11.4f - body_top_mm) / (11.4f - 3.05f), 0.0f, 1.12f);
  st.body_top_mm = body_top_mm;
  st.compression_pct = clampf((1.0f - body_top_mm / 6.02f) * 100.0f, 0.0f, 64.0f);
  if (body_top_mm > 6.02f) {
    st.compression_pct = clampf((11.4f - body_top_mm) / (11.4f - 3.18f) * 47.3f, 0.0f, 47.3f);
  }

  const float ventral_z = lerpf(3.60f, 0.44f, clampf(squeeze, 0.0f, 1.0f));
  const float plate_pitch = lerpf(0.24f, 0.032f, clampf(squeeze, 0.0f, 1.0f));

  // Head + compound eyes + sweeping sensory antennae
  Vec3 head_c = {body_x_mm + 0.9f, body_y_mm, ventral_z + 0.42f + (body_top_mm - ventral_z) * 0.36f};
  st.addEll(head_c, {2.35f, 1.95f, 0.92f}, 0.25f + head_pitch_extra_rad, 0.0f, 0.0f, MAT_CHITIN);
  st.addEll(head_c + Vec3(0.95f, -1.28f, 0.25f), {0.58f, 0.40f, 0.44f}, 0.0f, 0.0f, 0.0f, MAT_EYE);
  st.addEll(head_c + Vec3(0.95f, 1.28f, 0.25f), {0.58f, 0.40f, 0.44f}, 0.0f, 0.0f, 0.0f, MAT_EYE);

  float ant_sweep = 0.22f * std::sin(st.t_sec * 11.5f);
  for (int sgn : {-1, 1}) {
    Vec3 a0 = head_c + Vec3(1.5f, sgn * 0.85f, 0.14f);
    Vec3 a1 = a0 + Vec3(5.8f, sgn * (2.5f + ant_sweep * 1.4f), lerpf(1.4f, 0.18f, clampf(squeeze, 0.f, 1.f)) + 0.25f * std::cos(st.t_sec * 13.f + sgn));
    Vec3 a2 = a1 + Vec3(7.4f, sgn * (3.6f - ant_sweep * 1.6f), -0.25f);
    a1.z = std::max(0.18f, std::min(st.ceiling_mm - 0.18f, a1.z));
    a2.z = std::max(0.14f, std::min(st.ceiling_mm - 0.18f, a2.z));
    st.addCap(a0, a1, 0.15f, MAT_CHITIN);
    st.addCap(a1, a2, 0.10f, MAT_CHITIN);
  }

  // 6 overlapping rigid dorsal chitin plates (tergites) + 5 soft cyan arthrodial hinges
  const float x_off[6] = {-2.2f, -6.5f, -10.4f, -14.7f, -19.0f, -23.1f};
  const float rx_pl[6] = {3.65f, 2.55f, 2.55f, 2.65f, 2.55f, 2.45f};
  const float ry_pl[6] = {4.35f, 4.55f, 4.75f, 4.70f, 4.30f, 3.50f};
  for (int i = 0; i < 6; ++i) {
    float spread = clampf(squeeze, 0.f, 1.f) * 0.72f;
    float z_pl = body_top_mm - 0.24f - i * lerpf(0.22f, 0.06f, clampf(squeeze, 0.f, 1.f));
    float roll_i = (i == 0) ? pronotum_roll_rad : (pronotum_roll_rad * 0.35f);
    st.addEll({body_x_mm + x_off[i], body_y_mm, z_pl}, {rx_pl[i], ry_pl[i] + spread, 0.32f}, -plate_pitch, roll_i, 0.0f, MAT_CHITIN);
    if (i < 5) {
      float z_hg = z_pl - 0.34f;
      float hz_hg = clampf((body_top_mm - ventral_z) * 0.14f, 0.16f, 0.40f);
      st.addEll({body_x_mm + x_off[i] - 2.15f, body_y_mm, z_hg}, {1.35f, ry_pl[i] * 0.86f, hz_hg}, -plate_pitch * 0.5f, 0.0f, 0.0f, MAT_HINGE);
    }
  }

  // Ventral sternum / abdomen ellipsoid — sits flush underneath dorsal chitin shields at all heights!
  float belly_mid_z = ventral_z + (body_top_mm - ventral_z) * 0.47f;
  st.addEll({body_x_mm - 12.8f, body_y_mm, belly_mid_z}, {12.8f, 3.90f + squeeze * 0.85f, std::max(0.52f, (body_top_mm - ventral_z) * 0.49f)}, 0.0f, 0.0f, 0.0f, MAT_CHITIN);

  // Rear sensory cerci
  for (int sgn : {-1, 1}) {
    Vec3 c0 = {body_x_mm - 24.8f, body_y_mm + sgn * 1.45f, ventral_z + 0.42f};
    Vec3 c1 = {body_x_mm - 28.2f, body_y_mm + sgn * 2.55f, ventral_z + 0.52f};
    st.addCap(c0, c1, 0.19f, MAT_CHITIN);
  }

  // Legs!
  float sprawl = clampf(squeeze, 0.0f, 1.0f);
  st.claw_z_mm = 0.47f * smoothstep(0.58f, 0.92f, sprawl);
  st.spines_planted = (sprawl > 0.78f) ? 1 : 0;

  auto buildLeg = [&](int pair_idx, int side_sgn, float ph_local, bool hero_rear_lock) {
    // pair_idx: 0=front, 1=mid, 2=hind
    const float hip_x_rel[3] = {-4.6f, -9.4f, -14.5f};
    const float hip_y_rel[3] = {2.4f, 2.9f, 3.1f};
    const float span_y[3] = {4.8f, 6.2f, 7.2f};
    const float reach_x[3] = {3.2f, -0.6f, -5.0f};

    Vec3 hip = {body_x_mm + hip_x_rel[pair_idx], body_y_mm + side_sgn * hip_y_rel[pair_idx], ventral_z + 0.58f};

    if (hero_rear_lock) {
      // Exact world-locked tibial-spine contact (0.000 mm slip!) for Chapter IV closeup & replay!
      float lock_t = smoothstep(0.60f, 0.90f, sprawl);
      float sx = lerpf(body_x_mm - 18.8f, locked_spine_world_x, lock_t);
      float sy = body_y_mm + side_sgn * lerpf(5.8f, 8.85f, sprawl);
      float shin_tip_z = lerpf(1.45f, 0.40f, lock_t);
      Vec3 shin_dist = {sx, sy, shin_tip_z};
      Vec3 knee = {lerpf(hip.x - 1.2f, (hip.x + sx) * 0.5f + 1.0f, sprawl), side_sgn * lerpf(4.8f, 6.9f, sprawl) + body_y_mm, std::min(st.ceiling_mm - 0.38f, lerpf(5.6f, 2.15f, sprawl))};
      st.addCap(hip, knee, 0.48f, MAT_CHITIN);
      st.addCap(knee, shin_dist, 0.36f, MAT_CHITIN);

      // 3 backward-pointing golden tibial spines!
      Vec3 sdir = norm(shin_dist - knee);
      for (int k = 0; k < 3; ++k) {
        float u = 0.54f + 0.18f * k;
        Vec3 base = knee + (shin_dist - knee) * u;
        float tip_z = lerpf(base.z - 0.72f, 0.0f, smoothstep(0.75f, 0.92f, sprawl));
        Vec3 tip = {base.x - 0.36f - 0.10f * k + sdir.x * 0.08f, base.y + side_sgn * 0.14f, std::max(0.0f, tip_z)};
        st.addCap(base, tip, 0.135f, MAT_SPINE);
        if (tip.z <= 0.04f && st.num_glow_pts < 6) {
          st.spine_glow_pts[st.num_glow_pts++] = tip;
        }
      }

      // Distal tarsus + paired forked claws tipping sideways into the air (+0.47 mm)!
      float cz = st.claw_z_mm;
      Vec3 ankle = {sx - 1.25f, sy + side_sgn * lerpf(0.85f, 2.35f, sprawl), lerpf(0.32f, 0.58f, sprawl)};
      Vec3 foot = {ankle.x - 1.35f, ankle.y + side_sgn * lerpf(0.65f, 1.95f, sprawl), cz + 0.13f};
      st.addCap(shin_dist, ankle, 0.23f, MAT_CLAW);
      st.addCap(ankle, foot, 0.18f, MAT_CLAW);
      st.addCap(foot, foot + Vec3(-0.55f, side_sgn * 0.48f, 0.18f * sprawl), 0.10f, MAT_CLAW);
      st.addCap(foot, foot + Vec3(-0.28f, side_sgn * 0.68f, -0.05f), 0.10f, MAT_CLAW);
      return;
    }

    float cyc = std::sin(ph_local);
    float lift = std::max(0.0f, std::cos(ph_local)) * lerpf(1.35f, 0.25f, sprawl);
    float stride_amp = lerpf(2.55f, 1.55f, sprawl);
    Vec3 knee = {
        hip.x + reach_x[pair_idx] * 0.42f + stride_amp * 0.45f * cyc,
        body_y_mm + side_sgn * (span_y[pair_idx] * lerpf(0.68f, 0.92f, sprawl)),
        std::min(st.ceiling_mm - 0.36f, lerpf(4.8f, 1.85f, sprawl) + lift * 0.35f)};
    float contact_z = (sprawl > 0.78f) ? 0.36f : (0.16f + lift);
    Vec3 shin_end = {
        hip.x + reach_x[pair_idx] + stride_amp * cyc,
        body_y_mm + side_sgn * (span_y[pair_idx] + sprawl * 2.5f),
        contact_z};
    st.addCap(hip, knee, 0.40f, MAT_CHITIN);
    st.addCap(knee, shin_end, 0.29f, MAT_CHITIN);

    // Add visible golden shin spines on legs when compressed!
    if (sprawl > 0.55f) {
      Vec3 base = lerp3(knee, shin_end, 0.78f);
      Vec3 tip = {base.x - 0.38f, base.y + side_sgn * 0.12f, std::max(0.0f, contact_z - 0.36f)};
      st.addCap(base, tip, 0.11f, MAT_SPINE);
      if (tip.z <= 0.05f && st.num_glow_pts < 6 && pair_idx >= 1) {
        st.spine_glow_pts[st.num_glow_pts++] = tip;
      }
    }

    // Distal tarsus
    Vec3 tarsus_tip = {
        shin_end.x + (pair_idx == 0 ? 1.1f : -1.2f),
        shin_end.y + side_sgn * (0.85f + sprawl * 1.55f),
        (sprawl > 0.78f) ? (0.50f + lift * 0.2f) : (0.14f + lift)};
    st.addCap(shin_end, tarsus_tip, 0.18f, MAT_CLAW);
  };

  for (int p = 0; p < 3; ++p) {
    for (int side_idx = 0; side_idx < 2; ++side_idx) {
      int sgn = (side_idx == 0) ? -1 : 1;  // -1 = camera-right (-Y), +1 = camera-left (+Y)
      float ph = gait_phase;
      if (oar_midlegs && p == 1) {
        // Synchronous paired middle-leg oar shove!
        ph = gait_phase;
      } else if (tripod_mode) {
        // Alternating tripod: (L1, R2, L3) vs (R1, L2, R3)
        bool groupA = ((p + side_idx) % 2 == 0);
        ph = gait_phase + (groupA ? 0.0f : kPi);
      } else {
        // Metachronal / uncoupled confined crawl
        ph = gait_phase + p * 1.35f + side_idx * 2.1f;
      }
      bool hero_lock = rear_spine_lock && (p == 2) && (sgn == -1);
      buildLeg(p, sgn, ph, hero_lock);
    }
  }
}

void addPennies(SceneState& st, float x_mm, float y_mm) {
  // Two stacked US pennies: 19.05 mm diameter (r=9.525), 1.52 mm each = 3.04 mm total height
  st.addCyl({x_mm, y_mm, 0.76f}, 9.525f, 0.74f, MAT_PENNY);
  st.addCyl({x_mm + 0.35f, y_mm - 0.25f, 2.28f}, 9.525f, 0.74f, MAT_PENNY);
}

// Master 10,461-frame voice-locked directorial timeline across all 7 chapters!
SceneState solveTimeline(int frame) {
  SceneState st;
  st.frame = frame;
  st.t_sec = static_cast<float>(frame) / 30.0f;
  const float t = st.t_sec;

  // Gentle twilight fade-in / fade-out (never drops to dead-black luma < 2.0)
  st.fade_gain = lerpf(0.42f, 1.0f, smoothstep(0.0f, 0.55f, t)) *
                 lerpf(1.0f, 0.42f, smoothstep(346.5f, 348.7f, t));

  // Voice-locked chapter boundaries from `manifests/voice-lock.json`:
  // Ch1: 0..1056 (0.00..35.20s)
  // Ch2: 1056..2578 (35.20..85.93s)
  // Ch3: 2578..4135 (85.93..137.83s)
  // Ch4: 4135..6074 (137.83..202.47s)
  // Ch5: 6074..7617 (202.47..253.90s)
  // Ch6: 7617..9282 (253.90..309.40s)
  // Ch7: 9282..10461 (309.40..348.70s)

  if (frame < 1056) {
    // =========================================================================
    // CHAPTER I — UNDER THE DOOR (f0000..f1056, 0.00s..35.20s)
    // =========================================================================
    st.chapter = 1;
    st.floor_grit_mode = 3;  // Kitchen tile grid
    const float u = static_cast<float>(frame) / 1056.0f;

    // Closed door slab with 3.20 mm gap underneath (x in [0, 18], z in [3.20, 26.0])
    st.ceiling_mm = 3.20f;
    st.addSlab({0.0f, -38.0f, 3.20f}, {18.0f, 38.0f, 24.0f}, MAT_DOOR_WOOD, false);
    addPennies(st, -9.0f, 17.5f);

    if (u < 0.16f) {
      // Shot 1A (0..5.6s): Dark kitchen floor -> overhead light flips ON at t=0.85s -> roach bolts!
      st.subscene = 1;
      st.light_switch_on = 0.36f + 0.64f * smoothstep(0.65f, 0.92f, t);
      float q = u / 0.16f;
      float p = smoothstep(0.05f, 1.0f, q);
      float bx = lerpf(-38.0f, -4.0f, p);
      populateCockroach(st, bx, 0.0f, 11.4f, t * 34.0f, true, false, false, 0.0f, 0.0f, 0.0f);
      st.cam_pos = {bx - 22.0f + 3.5f * q, -24.0f + 2.5f * q, 9.5f - 0.8f * q};
      st.cam_target = {bx + 4.0f, 3.0f, 4.2f};
      st.fov_deg = 36.0f;
    } else if (u < 0.48f) {
      // Shot 1B (5.6..16.9s): Eye-level beside the two stacked pennies -> head dips in, back flattens, vanishes!
      st.subscene = 2;
      float p = (u - 0.16f) / 0.32f;
      float bx = lerpf(-12.0f, 46.0f, smoothstep(0.05f, 0.85f, p));
      float in_gap = smoothstep(-2.0f, 5.0f, bx) * (1.0f - smoothstep(20.0f, 32.0f, bx));
      float btop = lerpf(11.4f, 3.16f, in_gap);
      populateCockroach(st, bx, 0.0f, btop, t * 28.0f, in_gap < 0.5f, in_gap >= 0.5f, false, 0.0f, 0.0f, 0.25f * in_gap);
      st.cam_pos = {-24.0f + 8.0f * p, -21.0f + 5.0f * p, 5.8f - 1.8f * p};
      st.cam_target = {clampf(bx - 6.0f, -8.0f, 12.0f), 3.5f, 2.5f};
      st.fov_deg = 33.0f;
    } else {
      // Shot 1C (16.9..35.2s): Double Mechanical Paradox — slow macro orbit around compressed shell under 3.2 mm lip!
      st.subscene = 3;
      float p = (u - 0.48f) / 0.52f;
      st.num_slabs = 0;
      st.addSlab({-2.0f, -34.0f, 3.20f}, {20.0f, 34.0f, 3.75f}, MAT_DOOR_WOOD, true);
      float bx = lerpf(8.0f, 13.5f, p);
      populateCockroach(st, bx, 0.0f, 3.16f, t * 6.0f, false, true, false, 0.0f, 0.0f, 0.12f);
      float ang = lerpf(-1.25f, -0.60f, p);
      st.cam_pos = {bx - 10.0f + 25.0f * std::cos(ang), 25.0f * std::sin(ang), lerpf(9.5f, 6.8f, p)};
      st.cam_target = {bx - 10.5f, 2.0f, 2.0f};
      st.fov_deg = 33.0f;
    }

  } else if (frame < 2578) {
    // =========================================================================
    // CHAPTER II — FIVE MOVES THROUGH THE SLOT (f1056..f2578, 35.20s..85.93s)
    // =========================================================================
    st.chapter = 2;
    st.floor_grit_mode = 1;
    st.ceiling_mm = 3.20f;
    st.addSlab({0.0f, -34.0f, 3.20f}, {18.0f, 34.0f, 3.75f}, MAT_DOOR_WOOD, true);
    addPennies(st, -8.0f, 16.5f);
    const float u = static_cast<float>(frame - 1056) / 1522.0f;

    if (u < 0.58f) {
      st.subscene = 1;
      float p = u / 0.58f;
      float bx = lerpf(-6.5f, 34.0f, smoothstep(0.06f, 0.96f, p));
      float in_slot = smoothstep(-2.5f, 5.5f, bx) * (1.0f - smoothstep(22.0f, 33.0f, bx));
      float btop = lerpf(11.4f, 3.16f, in_slot);
      float pro_roll = 0.22f * std::sin(clampf((p - 0.22f) / 0.24f, 0.0f, 1.0f) * kPi);
      float head_wedge = 0.30f * std::sin(clampf((p - 0.10f) / 0.22f, 0.0f, 1.0f) * kPi);
      st.speed_cm_s = lerpf(58.0f, 14.5f, in_slot);
      populateCockroach(st, bx, 0.0f, btop, t * 7.5f, false, true, false, 0.0f, pro_roll, head_wedge);
      st.cam_pos = {lerpf(-22.0f, 6.0f, p), lerpf(-24.0f, -20.0f, p), lerpf(8.8f, 6.5f, p)};
      st.cam_target = {bx - 9.0f, 1.8f, 2.2f};
      st.fov_deg = 33.0f;
    } else {
      // Shot 2B: Sagittal roof-tile cutaway — stiff chitin plates overlapping on cyan soft hinges!
      st.subscene = 2;
      float p = (u - 0.58f) / 0.42f;
      float btop = lerpf(4.20f, 3.16f, 0.5f + 0.5f * std::sin(p * kPi * 1.5f));
      float bx = 12.0f + 5.0f * p;
      populateCockroach(st, bx, 0.0f, btop, t * 5.0f, false, true, false, 0.0f, 0.0f, 0.0f);
      st.cam_pos = {bx - 13.5f + 3.0f * p, -18.5f, 2.75f};
      st.cam_target = {bx - 11.5f + 2.5f * p, 0.0f, 1.95f};
      st.fov_deg = 28.0f;
    }

  } else if (frame < 4135) {
    // =========================================================================
    // CHAPTER III — THE LOW-CEILING SURPRISE (f2578..f4135, 85.93s..137.83s)
    // =========================================================================
    st.chapter = 3;
    st.floor_grit_mode = 1;
    const float u = static_cast<float>(frame - 2578) / 1557.0f;

    float ceil_mm = 12.0f;
    if (u < 0.25f) {
      ceil_mm = 12.0f;
      st.subscene = 1;
    } else if (u < 0.62f) {
      ceil_mm = lerpf(12.0f, 6.0f, smoothstep(0.25f, 0.48f, u));
      st.subscene = 2;
    } else {
      ceil_mm = lerpf(6.0f, 4.0f, smoothstep(0.62f, 0.76f, u));
      st.subscene = 3;
    }
    st.ceiling_mm = ceil_mm;
    st.addSlab({-30.0f, -26.0f, ceil_mm}, {55.0f, 26.0f, ceil_mm + 0.55f}, MAT_DOOR_WOOD, true);

    float btop = std::min(11.4f, ceil_mm - 0.16f);
    float crash = smoothstep(5.6f, 4.1f, ceil_mm);
    st.speed_cm_s = lerpf(58.05f, 14.52f, crash);
    float bx = -12.0f + lerpf(26.0f, 9.0f, crash) * u;
    float gait_ph = (crash < 0.5f) ? (t * 28.0f) : (t * 8.5f);
    populateCockroach(st, bx, 0.0f, btop, gait_ph, crash < 0.55f, crash >= 0.55f, false, 0.0f, 0.0f, 0.0f);

    st.cam_pos = {bx - 24.0f, -24.5f, std::min(ceil_mm - 0.85f, 4.8f)};
    st.cam_target = {bx - 10.5f, 0.0f, std::min(btop * 0.52f, 2.8f)};
    st.fov_deg = 34.0f;

  } else if (frame < 6074) {
    // =========================================================================
    // CHAPTER IV — WHEN SHINS BECOME FEET (f4135..f6074, 137.83s..202.47s)
    // =========================================================================
    st.chapter = 4;
    st.floor_grit_mode = 1;
    const float u = static_cast<float>(frame - 4135) / 1939.0f;

    if (u < 0.28f) {
      st.subscene = 1;
      st.ceiling_mm = 12.0f;
      float bx = lerpf(-6.0f, 6.0f, u / 0.28f);
      populateCockroach(st, bx, 0.0f, 11.4f, t * 12.0f, true, false, true, bx - 18.8f, 0.0f, 0.0f);
      st.cam_pos = {bx - 27.5f, -16.5f, 4.4f};
      st.cam_target = {bx - 17.5f, -5.8f, 1.5f};
      st.fov_deg = 29.0f;
    } else if (u < 0.72f) {
      st.subscene = 2;
      float p = (u - 0.28f) / 0.44f;
      float press = smoothstep(0.05f, 0.42f, p);
      st.ceiling_mm = lerpf(12.0f, 4.0f, press);
      st.addSlab({-26.0f, -26.0f, st.ceiling_mm}, {36.0f, 26.0f, st.ceiling_mm + 0.55f}, MAT_DOOR_WOOD, true);
      float push = smoothstep(0.42f, 0.96f, p);
      float bx = 6.0f + 5.6f * push;
      float btop = std::min(11.4f, st.ceiling_mm - 0.14f);
      st.speed_cm_s = lerpf(58.05f, 14.52f, press);
      populateCockroach(st, bx, 0.0f, btop, t * 7.0f, false, true, true, -12.8f, 0.0f, 0.0f);
      st.cam_pos = {lerpf(-22.5f, -20.5f, p), lerpf(-16.8f, -14.5f, p), 2.15f};
      st.cam_target = {-13.0f + 1.6f * push, -7.2f, 1.05f};
      st.fov_deg = 28.5f;
    } else {
      st.subscene = 3;
      float p = (u - 0.72f) / 0.28f;
      st.ceiling_mm = 4.0f;
      st.addSlab({-28.0f, -26.0f, 4.0f}, {38.0f, 26.0f, 4.50f}, MAT_DOOR_WOOD, true);
      float bx = 4.0f + 12.0f * p;
      st.speed_cm_s = 14.52f;
      st.load_bw_mult = 5.1f;
      populateCockroach(st, bx, 0.0f, 3.85f, t * 11.0f, false, true, false, 0.0f, 0.0f, 0.0f);
      st.cam_pos = {bx - 12.0f, -9.5f, 31.0f};
      st.cam_target = {bx - 11.0f, 0.0f, 2.0f};
      st.fov_deg = 38.0f;
    }

  } else if (frame < 7617) {
    // =========================================================================
    // CHAPTER V — THE ROUGH-FLOOR TRAP (f6074..f7617, 202.47s..253.90s)
    // =========================================================================
    st.chapter = 5;
    st.ceiling_mm = 4.0f;
    st.addSlab({-30.0f, -26.0f, 4.0f}, {42.0f, 26.0f, 4.55f}, MAT_DOOR_WOOD, true);
    const float u = static_cast<float>(frame - 6074) / 1543.0f;

    if (u < 0.34f) {
      st.subscene = 1;
      st.floor_grit_mode = 0;
      st.speed_cm_s = 1.57f;
      float bx = 4.0f + 2.2f * (u / 0.34f);
      populateCockroach(st, bx, 0.0f, 3.85f, t * 15.0f, false, true, false, 0.0f, 0.0f, 0.0f);
      st.cam_pos = {bx - 22.5f, -16.5f, 2.25f};
      st.cam_target = {bx - 11.5f, -4.5f, 1.15f};
      st.fov_deg = 30.0f;
    } else if (u < 0.66f) {
      st.subscene = 2;
      st.floor_grit_mode = 1;
      st.speed_cm_s = 5.26f;
      float p = (u - 0.34f) / 0.32f;
      float bx = 4.0f + 9.5f * p;
      populateCockroach(st, bx, 0.0f, 3.85f, t * 12.0f, false, true, true, 4.0f - 14.5f + 4.5f * std::floor(p * 2.0f), 0.0f, 0.0f);
      st.cam_pos = {bx - 22.5f, -16.5f, 2.20f};
      st.cam_target = {bx - 12.0f, -4.5f, 1.15f};
      st.fov_deg = 30.0f;
    } else {
      st.subscene = 3;
      st.floor_grit_mode = 2;
      st.speed_cm_s = 3.69f;
      float p = (u - 0.66f) / 0.34f;
      float bx = 4.0f + 5.2f * p + 0.32f * std::sin(p * 28.0f);
      for (int g = 0; g < 6; ++g) {
        float gx = -14.0f + g * 5.2f;
        float gy = (g % 2 == 0) ? -1.4f : 1.6f;
        st.addCyl({gx, gy, 0.24f}, 1.35f, 0.24f, MAT_BOULDER_GRIT);
      }
      populateCockroach(st, bx, 0.0f, 3.85f, t * 11.0f, false, true, false, 0.0f, 0.0f, 0.0f);
      st.cam_pos = {bx - 21.5f, -16.2f, 2.15f};
      st.cam_target = {bx - 11.0f, -1.5f, 1.05f};
      st.fov_deg = 30.0f;
    }

  } else if (frame < 9282) {
    // =========================================================================
    // CHAPTER VI — TOUGH SHELL, TIGHT LIMIT (f7617..f9282, 253.90s..309.40s)
    // =========================================================================
    st.chapter = 6;
    st.floor_grit_mode = 1;
    const float u = static_cast<float>(frame - 7617) / 1665.0f;

    if (u < 0.42f) {
      st.subscene = 1;
      float p = u / 0.42f;
      float press_wave = smoothstep(0.06f, 0.36f, p) * (1.0f - smoothstep(0.58f, 0.74f, p));
      float btop = lerpf(11.4f, 3.08f, press_wave);
      st.ceiling_mm = btop + 0.14f;
      st.load_bw_mult = 900.0f * press_wave;
      float sprint_after = smoothstep(0.74f, 0.98f, p);
      st.speed_cm_s = (sprint_after > 0.02f) ? 76.7f : 0.0f;
      float bx = 4.0f + 28.0f * sprint_after;
      if (p < 0.78f) {
        // Clear optical compression platen pressing directly onto dorsal plates + compact upper force piston!
        st.addSlab({-22.0f, -11.0f, btop + 0.08f}, {6.0f, 11.0f, btop + 0.72f}, MAT_LOAD_CELL, true);
        st.addCyl({-8.5f, 0.0f, btop + 3.60f}, 3.4f, 2.85f, MAT_LOAD_CELL);
      }
      populateCockroach(st, bx, 0.0f, btop, t * 26.0f * sprint_after + t * 2.0f, true, false, false, 0.0f, 0.0f, 0.0f);
      st.cam_pos = {-27.0f + 7.5f * p + 8.0f * sprint_after, -23.5f + 3.5f * p, 8.2f - 1.2f * p};
      st.cam_target = {bx - 10.5f, 0.0f, 3.0f};
      st.fov_deg = 34.0f;
    } else {
      st.subscene = (u < 0.72f) ? 2 : 3;
      st.ceiling_mm = 3.20f;
      st.addSlab({0.0f, -34.0f, 3.20f}, {18.0f, 34.0f, 3.75f}, MAT_DOOR_WOOD, true);
      addPennies(st, -8.5f, 16.5f);

      if (u < 0.72f) {
        float p = (u - 0.42f) / 0.30f;
        float approach = smoothstep(0.0f, 0.48f, p) - 0.75f * smoothstep(0.55f, 0.96f, p);
        float bx = lerpf(-16.0f, -1.8f, approach);
        populateCockroach(st, bx, 0.0f, 11.4f, t * 14.0f, true, false, false, 0.0f, 0.0f, 0.18f);
        st.cam_pos = {-28.0f + 5.5f * p, -21.5f + 3.0f * p, 8.0f - 0.8f * p};
        st.cam_target = {-5.0f + 1.5f * p, 3.5f, 3.0f};
        st.fov_deg = 34.0f;
      } else {
        float p = (u - 0.72f) / 0.28f;
        float enter = smoothstep(0.0f, 0.38f, p);
        float struggle = (p > 0.38f) ? (0.22f * std::sin(p * 36.0f)) : 0.0f;
        float bx = lerpf(-8.0f, 4.2f, enter) + struggle;
        float btop = lerpf(11.4f, 3.55f, enter);
        st.speed_cm_s = (p > 0.38f) ? 0.0f : 18.0f;
        populateCockroach(st, bx, 0.0f, btop, t * 18.0f, false, true, false, 0.0f, 0.08f, 0.22f);
        st.cam_pos = {-23.0f + 5.5f * p, -20.0f + 3.2f * p, 6.8f - 1.1f * p};
        st.cam_target = {-4.0f + 1.5f * p, 2.0f, 2.4f};
        st.fov_deg = 32.0f;
      }
    }

  } else {
    // =========================================================================
    // CHAPTER VII — HINGES AND SPINES (f9282..f10461, 309.40s..348.70s + 8s HOLD)
    // =========================================================================
    st.chapter = 7;
    st.floor_grit_mode = 1;
    st.ceiling_mm = 3.20f;
    st.addSlab({0.0f, -34.0f, 3.20f}, {18.0f, 34.0f, 3.75f}, MAT_DOOR_WOOD, true);
    addPennies(st, -8.5f, 16.5f);
    const float u = static_cast<float>(frame - 9282) / 1179.0f;

    float pass_p = smoothstep(0.02f, 0.62f, u);
    float sprint_out = smoothstep(0.62f, 1.00f, u);
    float bx = lerpf(-14.0f, 32.0f, pass_p) + 42.0f * sprint_out;
    float in_slot = smoothstep(-2.0f, 5.5f, bx) * (1.0f - smoothstep(20.0f, 31.0f, bx));
    float btop = lerpf(11.4f, 3.16f, in_slot);
    st.speed_cm_s = lerpf(58.05f, 14.52f, in_slot);
    populateCockroach(st, bx, 0.0f, btop, t * lerpf(26.0f, 9.0f, in_slot), in_slot < 0.5f, in_slot >= 0.5f, false, 0.0f, 0.0f, 0.16f * in_slot);

    st.cam_pos = {lerpf(-26.0f, 22.0f, u), lerpf(-23.5f, -17.5f, u), lerpf(8.2f, 5.2f, u)};
    st.cam_target = {lerpf(-6.0f, 42.0f, u), 3.0f, 2.8f};
    st.fov_deg = 34.0f;
  }

  return st;
}

// Fast 1-pass analytic occlusion shadow factor against cockroach ellipsoids & slabs
float analyticShadow(const Vec3& p, const Vec3& ldir, const SceneState& st) {
  Vec3 oc_r = p - st.roach_center;
  float b = dot(oc_r, ldir);
  float c = dot(oc_r, oc_r) - st.roach_bound_r * st.roach_bound_r;
  float sh = 1.0f;
  if (!(c > 0.0f && b > 0.0f) && (b * b - c >= 0.0f)) {
    float dummy_t;
    Vec3 dummy_n;
    for (int i = 0; i < st.num_ells; ++i) {
      if (hitEllipsoid(p, ldir, st.ells[i], 35.0f, dummy_t, dummy_n)) {
        sh = 0.24f;
        break;
      }
    }
    if (sh > 0.5f) {
      for (int i = 0; i < st.num_caps; ++i) {
        if (hitCapsule(p, ldir, st.caps[i], 35.0f, dummy_t, dummy_n)) {
          sh = 0.36f;
          break;
        }
      }
    }
  }
  for (int i = 0; i < st.num_cyls && sh > 0.3f; ++i) {
    float dt;
    Vec3 dn;
    if (hitCylinderZ(p, ldir, st.cyls[i], 35.0f, dt, dn)) sh = 0.24f;
  }
  for (int i = 0; i < st.num_slabs && sh > 0.3f; ++i) {
    float tn, tf;
    Vec3 dn;
    if (hitBox(p, ldir, st.slabs[i].bmin, st.slabs[i].bmax, tn, tf, dn) && tf > 0.02f) {
      sh = std::min(sh, st.slabs[i].translucent ? 0.76f : 0.22f);
    }
  }
  return sh;
}

Vec3 shadeRay(const Vec3& ro, const Vec3& rd, const SceneState& st) {
  float best_t = 1e9f;
  Vec3 best_n = {0.0f, 0.0f, 1.0f};
  int best_mat = MAT_SKY;

  // 1. Analytic z=0 floor plane
  if (rd.z < -1e-5f) {
    float tf = -ro.z / rd.z;
    if (tf > 0.005f && tf < 140.0f) {
      best_t = tf;
      best_n = {0.0f, 0.0f, 1.0f};
      best_mat = MAT_FLOOR;
    }
  }

  // 2. Opaque slabs (e.g., wooden door in Ch1)
  for (int i = 0; i < st.num_slabs; ++i) {
    if (!st.slabs[i].translucent) {
      float tn, tf;
      Vec3 nn;
      if (hitBox(ro, rd, st.slabs[i].bmin, st.slabs[i].bmax, tn, tf, nn)) {
        float thit = (tn > 0.005f) ? tn : tf;
        if (thit > 0.005f && thit < best_t) {
          best_t = thit;
          best_n = nn;
          best_mat = st.slabs[i].mat;
        }
      }
    }
  }

  // 3. Cylinders (two copper pennies, load anvil, coarse boulders)
  for (int i = 0; i < st.num_cyls; ++i) {
    float tc;
    Vec3 nc;
    if (hitCylinderZ(ro, rd, st.cyls[i], best_t, tc, nc)) {
      best_t = tc;
      best_n = nc;
      best_mat = st.cyls[i].mat;
    }
  }

  // 4. Cockroach bounding-sphere early reject -> exact ellipsoids + capsules!
  Vec3 oc_r = ro - st.roach_center;
  float br = dot(oc_r, rd);
  float cr = dot(oc_r, oc_r) - st.roach_bound_r * st.roach_bound_r;
  if (!(cr > 0.0f && br > 0.0f) && (br * br - cr >= 0.0f)) {
    for (int i = 0; i < st.num_ells; ++i) {
      float te;
      Vec3 ne;
      if (hitEllipsoid(ro, rd, st.ells[i], best_t, te, ne)) {
        best_t = te;
        best_n = ne;
        best_mat = st.ells[i].mat;
      }
    }
    for (int i = 0; i < st.num_caps; ++i) {
      float tc;
      Vec3 nc;
      if (hitCapsule(ro, rd, st.caps[i], best_t, tc, nc)) {
        best_t = tc;
        best_n = nc;
        best_mat = st.caps[i].mat;
      }
    }
  }

  const Vec3 key_dir = norm({-0.44f, -0.58f, 0.68f});
  const Vec3 rim_dir = norm({0.68f, 0.50f, 0.53f});

  Vec3 col;
  if (best_mat == MAT_SKY) {
    float h = clampf(rd.z * 2.2f + 0.2f, 0.0f, 1.0f);
    col = lerp3({0.022f, 0.032f, 0.050f}, {0.008f, 0.013f, 0.022f}, h);
  } else {
    Vec3 p = ro + rd * best_t;
    Vec3 n = best_n;
    Vec3 v = rd * -1.0f;

    Vec3 base = {0.5f, 0.5f, 0.5f};
    float spec_str = 0.35f;
    float shininess = 32.0f;

    if (best_mat == MAT_FLOOR) {
      float fade = std::exp(-0.020f * best_t);
      float gx = std::fabs(std::fmod(std::fabs(p.x) + 1000.0f, 5.0f) - 2.5f);
      float gy = std::fabs(std::fmod(std::fabs(p.y) + 1000.0f, 5.0f) - 2.5f);
      float grid = (std::min(gx, gy) < 0.055f) ? 1.0f : 0.0f;

      if (st.floor_grit_mode == 0) {
        // Slick mirror acrylic floor
        base = lerp3({0.030f, 0.042f, 0.062f}, {0.060f, 0.085f, 0.120f}, grid * fade);
        spec_str = 0.72f;
        shininess = 96.0f;
      } else if (st.floor_grit_mode == 2) {
        // Coarse 20-grit mineral floor
        float gnoise = std::sin(p.x * 3.8f) * std::cos(p.y * 3.8f);
        base = lerp3({0.042f, 0.048f, 0.058f}, {0.088f, 0.095f, 0.110f}, 0.5f + 0.5f * gnoise * fade);
        n = norm({-0.12f * std::cos(p.x * 3.8f) * fade, 0.12f * std::sin(p.y * 3.8f) * fade, 1.0f});
        spec_str = 0.14f;
      } else if (st.floor_grit_mode == 3) {
        // Warm kitchen nocturnal tile
        float tile_line = (std::min(std::fabs(std::fmod(std::fabs(p.x) + 1000.f, 22.0f) - 11.0f),
                                    std::fabs(std::fmod(std::fabs(p.y) + 1000.f, 22.0f) - 11.0f)) < 0.18f)
                              ? 1.0f
                              : 0.0f;
        base = lerp3({0.038f, 0.042f, 0.052f}, {0.018f, 0.020f, 0.026f}, tile_line * fade);
        spec_str = 0.42f;
      } else {
        // Calibrated 40-grit mineral test deck + 5 mm scale grid
        float grit = std::sin(p.x * 9.5f) * std::sin(p.y * 9.5f);
        base = lerp3({0.032f, 0.042f, 0.058f}, {0.068f, 0.092f, 0.128f}, grid * fade);
        base = base + Vec3(0.007f, 0.008f, 0.010f) * (grit * fade);
        n = norm({-0.05f * std::cos(p.x * 9.5f) * fade, -0.05f * std::cos(p.y * 9.5f) * fade, 1.0f});
        spec_str = 0.22f;
      }
    } else if (best_mat == MAT_CHITIN) {
      float band = 0.5f + 0.5f * std::sin(p.x * 1.15f);
      base = lerp3({0.46f, 0.20f, 0.050f}, {0.64f, 0.31f, 0.088f}, band);
      spec_str = 0.68f;
      shininess = 46.0f;
    } else if (best_mat == MAT_HINGE) {
      base = {0.075f, 0.58f, 0.52f};
      spec_str = 0.28f;
      shininess = 20.0f;
    } else if (best_mat == MAT_SPINE) {
      base = {0.98f, 0.78f, 0.20f};
      spec_str = 0.85f;
      shininess = 64.0f;
    } else if (best_mat == MAT_CLAW) {
      base = {0.64f, 0.77f, 0.88f};
      spec_str = 0.35f;
    } else if (best_mat == MAT_PENNY) {
      base = {0.76f, 0.36f, 0.18f};
      spec_str = 0.86f;
      shininess = 56.0f;
    } else if (best_mat == MAT_EYE) {
      base = {0.020f, 0.024f, 0.032f};
      spec_str = 0.95f;
      shininess = 96.0f;
    } else if (best_mat == MAT_DOOR_WOOD) {
      float grain = 0.5f + 0.5f * std::sin(p.y * 0.8f + std::sin(p.z * 1.4f));
      base = lerp3({0.18f, 0.11f, 0.07f}, {0.25f, 0.16f, 0.10f}, grain);
      spec_str = 0.24f;
    } else if (best_mat == MAT_LOAD_CELL) {
      base = {0.36f, 0.42f, 0.50f};
      spec_str = 0.82f;
      shininess = 72.0f;
    } else if (best_mat == MAT_BOULDER_GRIT) {
      base = {0.22f, 0.24f, 0.28f};
      spec_str = 0.18f;
    }

    float sh = analyticShadow(p + n * 0.03f, key_dir, st);
    float ndl = std::max(0.0f, dot(n, key_dir));
    float rim = std::max(0.0f, dot(n, rim_dir));
    Vec3 h_vec = norm(key_dir + v);
    float spec = std::pow(std::max(0.0f, dot(n, h_vec)), shininess) * spec_str * sh;
    float fres = std::pow(1.0f - std::max(0.0f, dot(n, v)), 3.0f);

    col = base * (0.18f + 0.94f * ndl * sh) + mul3(base, {0.42f, 0.56f, 0.76f}) * (0.34f * rim) +
          Vec3(1.0f, 0.96f, 0.88f) * spec + Vec3(0.08f, 0.14f, 0.22f) * (0.20f * fres);

    // Subtle warm golden floor halo right where tibial spines lock at z=0.00 mm!
    if (best_mat == MAT_FLOOR && st.num_glow_pts > 0) {
      for (int g = 0; g < st.num_glow_pts; ++g) {
        float d = len(p - st.spine_glow_pts[g]);
        col = col + Vec3(0.45f, 0.30f, 0.06f) * std::exp(-2.0f * d * d);
      }
    }
  }

  // 5. Analytic translucent cyan acrylic ceiling slab overlay
  for (int i = 0; i < st.num_slabs; ++i) {
    if (st.slabs[i].translucent) {
      float tn, tf;
      Vec3 nn;
      if (hitBox(ro, rd, st.slabs[i].bmin, st.slabs[i].bmax, tn, tf, nn)) {
        if (tn < best_t && tf > 0.005f) {
          float enter_t = std::max(0.0f, tn);
          float exit_t = std::min(best_t, tf);
          if (exit_t > enter_t) {
            Vec3 v = rd * -1.0f;
            float fres_g = std::pow(1.0f - std::fabs(dot(nn, v)), 4.0f);
            float edge = (std::fabs(nn.z) < 0.5f) ? 0.34f : 0.055f;
            col = lerp3(col, {0.22f, 0.72f, 0.88f}, clampf(edge + 0.14f * fres_g, 0.04f, 0.38f));
          }
        }
      }
    }
  }

  col = col * st.light_switch_on * st.fade_gain;
  return col;
}

inline uint8_t finishByte(float linear_c, float vig) {
  // ACES-inspired filmic curve + clean studio black floor (#0D131D)
  float x = std::max(0.0f, linear_c * 1.25f);
  float mapped = (x * (2.51f * x + 0.03f)) / (x * (2.43f * x + 0.59f) + 0.14f);
  float g = std::pow(clampf(mapped, 0.0f, 1.0f), 1.0f / 2.15f) * vig;
  return static_cast<uint8_t>(clampf(std::round(g * 255.0f), 0.0f, 255.0f));
}

}  // namespace

int main(int argc, char** argv) {
  int width = 1280;
  int height = 720;
  int first_frame = 0;
  int end_frame = 10461;
  int step_frame = 1;
  std::string out_raw_path = "feature_native.rgb";
  std::string csv_path = "feature_trace.csv";

  for (int i = 1; i < argc; ++i) {
    std::string arg = argv[i];
    if (arg == "--width" && i + 1 < argc) width = std::atoi(argv[++i]);
    else if (arg == "--height" && i + 1 < argc) height = std::atoi(argv[++i]);
    else if (arg == "--first" && i + 1 < argc) first_frame = std::atoi(argv[++i]);
    else if (arg == "--end" && i + 1 < argc) end_frame = std::atoi(argv[++i]);
    else if (arg == "--step" && i + 1 < argc) step_frame = std::atoi(argv[++i]);
    else if (arg == "--out-raw" && i + 1 < argc) out_raw_path = argv[++i];
    else if (arg == "--trace-csv" && i + 1 < argc) csv_path = argv[++i];
  }

  std::ofstream raw_file;
  std::ostream* raw_out_ptr = nullptr;
  if (out_raw_path == "-") {
    raw_out_ptr = &std::cout;
  } else {
    raw_file.open(out_raw_path, std::ios::binary);
    if (!raw_file) {
      std::cerr << "Failed to open raw output path\n";
      return 1;
    }
    raw_out_ptr = &raw_file;
  }
  std::ofstream csv_out(csv_path);
  if (!csv_out) {
    std::cerr << "Failed to open CSV output path\n";
    return 1;
  }

  csv_out << "frame,t_sec,chapter,subscene,ceiling_mm,body_top_mm,compression_pct,speed_cm_s,claw_z_mm,spines_planted,load_bw_mult,floor_grit_mode\n";
  std::vector<uint8_t> buf(static_cast<size_t>(width) * height * 3);
  const float aspect = static_cast<float>(width) / static_cast<float>(height);

  for (int f = first_frame; f < end_frame; f += step_frame) {
    SceneState st = solveTimeline(f);
    csv_out << f << "," << st.t_sec << "," << st.chapter << "," << st.subscene << ","
            << st.ceiling_mm << "," << st.body_top_mm << "," << st.compression_pct << ","
            << st.speed_cm_s << "," << st.claw_z_mm << "," << st.spines_planted << ","
            << st.load_bw_mult << "," << st.floor_grit_mode << "\n";

    Vec3 fwd = norm(st.cam_target - st.cam_pos);
    Vec3 right = norm(cross(fwd, {0.0f, 0.0f, 1.0f}));
    Vec3 up = cross(right, fwd);
    float half_h = std::tan((st.fov_deg * kPi / 180.0f) * 0.5f);
    float half_w = half_h * aspect;

#pragma omp parallel for schedule(dynamic, 8)
    for (int y = 0; y < height; ++y) {
      float ny_v = (static_cast<float>(y) / height) * 2.0f - 1.0f;
      for (int x = 0; x < width; ++x) {
        float nx_v = (static_cast<float>(x) / width) * 2.0f - 1.0f;
        float vig = clampf(1.0f - 0.20f * (nx_v * nx_v * 0.75f + ny_v * ny_v * 0.95f), 0.74f, 1.0f);

        // Adaptive 2x supersampling: full 2x AA near cockroach/objects, 1x on smooth analytic sky/floor!
        float u0 = ((x + 0.35f) / static_cast<float>(width)) * 2.0f - 1.0f;
        float v0 = 1.0f - ((y + 0.35f) / static_cast<float>(height)) * 2.0f;
        Vec3 rd0 = norm(fwd + right * (u0 * half_w) + up * (v0 * half_h));
        Vec3 acc = shadeRay(st.cam_pos, rd0, st);

        Vec3 oc_aa = st.cam_pos - st.roach_center;
        float b_aa = dot(oc_aa, rd0);
        float c_aa = dot(oc_aa, oc_aa) - (st.roach_bound_r + 3.0f) * (st.roach_bound_r + 3.0f);
        if (!(c_aa > 0.0f && b_aa > 0.0f) && (b_aa * b_aa - c_aa >= 0.0f)) {
          float u1 = ((x + 0.75f) / static_cast<float>(width)) * 2.0f - 1.0f;
          float v1 = 1.0f - ((y + 0.75f) / static_cast<float>(height)) * 2.0f;
          Vec3 rd1 = norm(fwd + right * (u1 * half_w) + up * (v1 * half_h));
          acc = (acc + shadeRay(st.cam_pos, rd1, st)) * 0.5f;
        }

        size_t idx = (static_cast<size_t>(y) * width + x) * 3;
        buf[idx + 0] = finishByte(acc.x, vig);
        buf[idx + 1] = finishByte(acc.y, vig);
        buf[idx + 2] = finishByte(acc.z, vig);
      }
    }

    raw_out_ptr->write(reinterpret_cast<const char*>(buf.data()), buf.size());
  }
  raw_out_ptr->flush();
  return 0;
}
