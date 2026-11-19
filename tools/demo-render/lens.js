import * as THREE from 'three';

export function lensStage(renderer) {
  const post = new THREE.Scene();
  const ortho = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 2);
  ortho.position.z = 1;
  let target;
  const uniforms = {
    plate: { value: null }, depths: { value: null }, stepUV: { value: new THREE.Vector2() },
    cameraNear: { value: .07 }, cameraFar: { value: 90 }, focalPlane: { value: 5 }, aperture: { value: 7 },
    bloom: { value: .7 }, exposure: { value: 1 }, shutter: { value: 0 }, moment: { value: 0 },
  };
  const opticalPrint = new THREE.ShaderMaterial({
    uniforms,
    depthTest: false, depthWrite: false,
    vertexShader: `varying vec2 uv2; void main(){ uv2=uv; gl_Position=vec4(position.xy,0.,1.); }`,
    fragmentShader: `
      varying vec2 uv2;
      uniform sampler2D plate, depths;
      uniform vec2 stepUV;
      uniform float cameraNear, cameraFar, focalPlane, aperture, bloom, exposure, shutter, moment;
      vec3 take(vec2 delta) { return texture2D(plate, clamp(uv2+delta, vec2(0.001),vec2(0.999))).rgb; }
      vec3 hot(vec2 delta) { return max(take(delta)-vec3(1.05),vec3(0.)); }
      void main(){
        float z=texture2D(depths,uv2).r;
        float viewZ=(cameraNear*cameraFar)/(cameraFar-z*(cameraFar-cameraNear));
        float coc=min(3.8, aperture*abs(viewZ-focalPlane)/max(1.0,viewZ)*0.37);
        vec2 radius=stepUV*(coc+.22);
        vec3 color=take(vec2(0.));
        if(coc<1.2){
          vec3 n=take(vec2(0.,stepUV.y)); vec3 s=take(vec2(0.,-stepUV.y));
          vec3 e=take(vec2(stepUV.x,0.)); vec3 w=take(vec2(-stepUV.x,0.));
          vec3 weights=vec3(.2126,.7152,.0722);
          float l=dot(color,weights);
          float gx=abs(dot(e,weights)-l)+abs(dot(w,weights)-l);
          float gy=abs(dot(n,weights)-l)+abs(dot(s,weights)-l);
          float soften=smoothstep(.06,.48,max(gx,gy))*.25;
          color=mix(color, gx>gy ? (e+w)*.5 : (n+s)*.5, soften);
        }
        if(coc>.27 || shutter>.15){
          vec2 travel=vec2(shutter*stepUV.x,-shutter*.48*stepUV.y);
          color=.52*color+.12*take(vec2(radius.x,radius.y)+travel)+.12*take(vec2(-radius.x,-radius.y)-travel)
             +.12*take(vec2(radius.x,-radius.y))+.12*take(vec2(-radius.x,radius.y));
        }
        vec2 scatter=stepUV*3.25;
        vec3 veil=(hot(vec2(scatter.x,0.))+hot(vec2(-scatter.x,0.))+hot(vec2(0.,scatter.y))+hot(vec2(0.,-scatter.y)))*.25;
        color += bloom*.34*veil*vec3(1.08,.91,.79);
        vec2 edge=(uv2-vec2(.5,.5))*vec2(1.15,.81);
        color *= exposure*(1.-dot(edge,edge)*.59);
        color *= vec3(1.024,.988,1.017);
        gl_FragColor=vec4(color,1.);
        #include <tonemapping_fragment>
        #include <colorspace_fragment>
        float film=fract(sin(dot(gl_FragCoord.xy+moment*vec2(19.2,7.91),vec2(12.9898,78.233)))*43758.5453)-.5;
        gl_FragColor.rgb += film*.012;
      }`,
  });
  post.add(new THREE.Mesh(new THREE.PlaneGeometry(2, 2), opticalPrint));

  return function expose(scene, cam, width, height, time) {
    if (!target || target.width !== width || target.height !== height) {
      target?.dispose();
      target = new THREE.WebGLRenderTarget(width, height, {
        type: THREE.HalfFloatType,
        depthBuffer: true,
        depthTexture: new THREE.DepthTexture(width, height, THREE.UnsignedIntType),
      });
      renderer.setSize(width, height, false);
      uniforms.plate.value = target.texture;
      uniforms.depths.value = target.depthTexture;
      uniforms.stepUV.value.set(1 / width, 1 / height);
    }
    const optic = cam.userData.lens;
    uniforms.cameraNear.value = cam.near;
    uniforms.cameraFar.value = cam.far;
    uniforms.focalPlane.value = optic.focus;
    uniforms.aperture.value = optic.aperture;
    uniforms.bloom.value = optic.bloom;
    uniforms.exposure.value = optic.exposure;
    uniforms.shutter.value = optic.smear;
    uniforms.moment.value = time;
    renderer.setRenderTarget(target);
    renderer.render(scene, cam);
    renderer.setRenderTarget(null);
    renderer.render(post, ortho);
  };
}
