/* Home page: 3D piano scroll story (Three.js 0.160, loaded as an ES module from jsDelivr).
   Copied from the Nov 17-19 landing prototype. Model: "Baby Grand Piano" by Roy_1508348
   (Blend Swap #29080, CC0), logo removed, own strings texture, sheet music added. */
import * as THREE from 'three';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { MeshoptDecoder } from 'three/addons/libs/meshopt_decoder.module.js';

const root = document.documentElement;
root.classList.add('js');
const reduceMQ = matchMedia('(prefers-reduced-motion: reduce)');
const darkMQ = matchMedia('(prefers-color-scheme: dark)');

/* ---------- text reveals (IntersectionObserver) ---------- */
const io = new IntersectionObserver((entries) => {
  for (const e of entries) if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); }
}, { threshold: 0.3 });
document.querySelectorAll('.reveal, .grow, .card-demo').forEach(el => io.observe(el));
document.getElementById('replay').addEventListener('click', () => {
  const d = document.getElementById('cardDemo');
  d.classList.remove('in'); void d.offsetWidth; d.classList.add('in');
});

/* ---------- theme: follows device, toggle overrides ---------- */
const themeBtn = document.getElementById('theme');
try { const saved = localStorage.getItem('ll-theme'); if (saved) root.dataset.theme = saved; } catch (e) {}
const currentTheme = () => root.dataset.theme || (darkMQ.matches ? 'dark' : 'light');
let onThemeChange = () => {};
function syncTheme() {
  const dark = currentTheme() === 'dark';
  themeBtn.textContent = dark ? 'Light' : 'Dark';
  themeBtn.setAttribute('aria-label', dark ? 'Switch to light mode' : 'Switch to dark mode');
  themeBtn.setAttribute('aria-pressed', String(dark));
  onThemeChange(dark);
}
themeBtn.addEventListener('click', () => {
  const next = currentTheme() === 'dark' ? 'light' : 'dark';
  root.dataset.theme = next;
  try { localStorage.setItem('ll-theme', next); } catch (e) {}
  syncTheme();
});
darkMQ.addEventListener('change', syncTheme);
syncTheme();

/* ---------- motion: follows the device's reduced-motion setting, button overrides ---------- */
const motionBtn = document.getElementById('motion');
let motionPref = null;
try { motionPref = localStorage.getItem('ll-motion'); } catch (e) {}
const motionOn = () => motionPref ? motionPref === 'on' : !reduceMQ.matches;
function syncMotion() {
  const on = motionOn();
  motionBtn.textContent = on ? 'Motion on' : 'Motion off';
  motionBtn.setAttribute('aria-pressed', String(on));
}
motionBtn.addEventListener('click', () => {
  motionPref = motionOn() ? 'off' : 'on';
  try { localStorage.setItem('ll-motion', motionPref); } catch (e) {}
  syncMotion();
});
reduceMQ.addEventListener('change', syncMotion);
syncMotion();
const diag = { renders: 0, err: '', cam: null };   // counters kept for debugging in DevTools

/* ---------- scroll progress + chapter counter ---------- */
const scroller = document.getElementById('scroller');
const chapters = [...document.querySelectorAll('.chapter')];
const progressEl = document.getElementById('progress');
const counterEl = document.getElementById('counter');
// Scroll progress is read from where each chapter sits on screen, so it works whichever element
// scrolls (the page, the in-page scroller, or a wrapper added by the host).
function scrollT() {
  const tops = chapters.map(c => c.getBoundingClientRect().top);
  if (tops[0] >= 0) return 0;
  for (let i = 0; i < tops.length - 1; i++) {
    if (tops[i + 1] > 0) return i + (-tops[i]) / (tops[i + 1] - tops[i]);
  }
  return tops.length - 1;
}
const computeAnchors = () => {};
computeAnchors();
let lastIdx = -1;
function updateChrome() {
  progressEl.style.transform = `scaleX(${scrollT() / (chapters.length - 1)})`;
  const idx = Math.round(scrollT());
  if (idx !== lastIdx) { counterEl.textContent = `${String(idx + 1).padStart(2, '0')} / ${String(chapters.length).padStart(2, '0')}`; lastIdx = idx; }
}
document.addEventListener('scroll', updateChrome, { passive: true, capture: true });  // catches scrolling on any element
addEventListener('resize', () => { computeAnchors(); updateChrome(); });
updateChrome();
/* ---------- glide to the next section as soon as the visitor scrolls ---------- */
const touch = matchMedia('(pointer: coarse)').matches;
if (touch) scroller.classList.add('snap');        // phones/iPads: the browser's own paging (smooth, direction-aware)
const scrollEl = () => (scroller.scrollHeight > scroller.clientHeight + 1 ? scroller : document.scrollingElement);
let settled = 0, gliding = false, lastWheel = 0, wheelBlocked = false, idleTimer = 0;
const easeInOut = (x) => x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2;
function glideTo(i) {
  i = Math.max(0, Math.min(chapters.length - 1, i));
  settled = i;
  const el = scrollEl(), from = el.scrollTop, to = chapters[i].offsetTop;
  if (Math.abs(to - from) < 2) return;
  if (!motionOn()) { el.scrollTop = to; return; }
  if (touch) { el.scrollTo({ top: to, behavior: 'smooth' }); return; }
  gliding = true;
  const dur = 750, t0 = performance.now();
  (function step(now) {
    const p = Math.min(1, (now - t0) / dur);
    el.scrollTop = from + (to - from) * easeInOut(p);
    if (p < 1) requestAnimationFrame(step); else gliding = false;
  })(t0);
}
// inside a section taller than the screen (long text on small screens), let the visitor read it first
function readingTallSection(dir) {
  const ch = chapters[settled];
  if (!ch || ch.offsetHeight <= innerHeight * 1.05) return false;
  const r = ch.getBoundingClientRect();
  return dir > 0 ? r.bottom > innerHeight + 2 : r.top < -2;
}
function intent(dir) {
  if (gliding) return true;
  if (readingTallSection(dir)) return false;
  glideTo(settled + dir);
  return true;
}
// mouse wheel / trackpad: the first movement starts the glide; the rest of that flick is swallowed
addEventListener('wheel', (e) => {
  if (touch) return;
  const now = performance.now(), quiet = now - lastWheel > 220;
  lastWheel = now;
  if (gliding || (wheelBlocked && !quiet)) { e.preventDefault(); return; }
  wheelBlocked = false;
  if (Math.abs(e.deltaY) < 2) return;
  if (intent(Math.sign(e.deltaY))) { e.preventDefault(); wheelBlocked = true; }
}, { passive: false });
// keyboard paging
addEventListener('keydown', (e) => {
  const dir = { ArrowDown: 1, PageDown: 1, ' ': e.shiftKey ? -1 : 1, ArrowUp: -1, PageUp: -1 }[e.key];
  if (!dir || touch || e.target.closest('input, textarea, select')) return;
  if (intent(dir)) e.preventDefault();
});
// dragging the scrollbar: keep track of where the visitor ended up
document.addEventListener('scroll', () => {
  if (gliding) return;
  clearTimeout(idleTimer);
  idleTimer = setTimeout(() => { if (!gliding) settled = Math.round(scrollT()); }, 160);
}, { passive: true, capture: true });
document.querySelectorAll('a[href^="#"]').forEach(link => link.addEventListener('click', (e) => {
  const href = link.getAttribute('href');
  if (href === '#top') { e.preventDefault(); glideTo(0); return; }
  const target = document.querySelector(href), idx = chapters.indexOf(target && target.closest('.chapter'));
  if (idx >= 0) { e.preventDefault(); glideTo(idx); }
}));

/* ---------- 3D piano ---------- */
start().catch(() => document.body.classList.add('no-webgl'));

async function start() {
  const canvas = document.getElementById('scene');
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
  const mobile = matchMedia('(pointer: coarse)').matches;
  renderer.setPixelRatio(Math.min(devicePixelRatio, mobile ? 1.5 : 2));
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.0;

  const scene = new THREE.Scene();
  const pmrem = new THREE.PMREMGenerator(renderer);
  scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;

  const camera = new THREE.PerspectiveCamera(32, innerWidth / innerHeight, 0.05, 60);

  scene.add(new THREE.HemisphereLight(0xffffff, 0x223344, 0.55));
  const key = new THREE.DirectionalLight(0xffffff, 1.6);
  key.position.set(3, 6, 4);
  key.castShadow = true;
  key.shadow.mapSize.set(mobile ? 1024 : 2048, mobile ? 1024 : 2048);
  Object.assign(key.shadow.camera, { left: -3, right: 3, top: 3, bottom: -3, near: 1, far: 15 });
  key.shadow.bias = -0.0005;
  scene.add(key);
  const fill = new THREE.DirectionalLight(0xffffff, 0.45);
  fill.position.set(0, 1.2, 6);
  scene.add(fill);
  const rim = new THREE.DirectionalLight(0x9BBDE6, 0.0);
  rim.position.set(-4, 3, -4);
  scene.add(rim);

  // stage light (dark mode): a soft spotlight from above, a faint beam and a pool of light on a black floor
  const spot = new THREE.SpotLight(0xfff1dc, 0, 12, 0.42, 0.65, 1.2);
  spot.position.set(0.3, 5.2, 1.4);
  spot.target.position.set(0, 0.6, 0);
  spot.castShadow = true;
  spot.shadow.mapSize.set(mobile ? 1024 : 2048, mobile ? 1024 : 2048);
  spot.shadow.bias = -0.0004;
  scene.add(spot, spot.target);
  const beam = (() => {
    const c = document.createElement('canvas'); c.width = 4; c.height = 256;
    const g = c.getContext('2d'), grad = g.createLinearGradient(0, 0, 0, 256);
    grad.addColorStop(0, 'rgba(255,241,220,0.55)'); grad.addColorStop(1, 'rgba(255,241,220,0)');
    g.fillStyle = grad; g.fillRect(0, 0, 4, 256);
    const tex = new THREE.CanvasTexture(c);
    const len = spot.position.distanceTo(spot.target.position) + 0.6;
    const geo = new THREE.CylinderGeometry(0.06, Math.tan(0.42) * len, len, 48, 1, true);
    geo.translate(0, -len / 2, 0);
    const mat = new THREE.MeshBasicMaterial({ map: tex, transparent: true, opacity: 0.3, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide });
    const m = new THREE.Mesh(geo, mat);
    m.position.copy(spot.position);
    m.lookAt(spot.target.position); m.rotateX(-Math.PI / 2);   // point the cone's tip at the lamp, mouth at the piano
    m.visible = false;
    return m;
  })();
  scene.add(beam);
  // the room: a seamless "infinity cove" (floor curving up into the walls, no corners or edges),
  // made by spinning a profile line around the vertical axis
  const R = 16, F = 4, H = 40, prof = [new THREE.Vector2(0.001, 0), new THREE.Vector2(R, 0)];
  for (let i = 1; i <= 20; i++) { const a = (i / 20) * Math.PI / 2; prof.push(new THREE.Vector2(R + Math.sin(a) * F, F - Math.cos(a) * F)); }
  prof.push(new THREE.Vector2(R + F, H));
  const roomMat = new THREE.MeshStandardMaterial({ color: 0xf1f2ef, roughness: 0.95, metalness: 0, envMapIntensity: 0, side: THREE.DoubleSide });
  const floor = new THREE.Mesh(new THREE.LatheGeometry(prof, 128), roomMat);
  floor.receiveShadow = true;
  scene.add(floor);

  // wait briefly for web fonts so the paper textures use them
  await Promise.race([
    Promise.all([document.fonts.load('500 40px Newsreader'), document.fonts.load('italic 400 20px Newsreader'), document.fonts.load('400 24px "Atkinson Hyperlegible Next"'),
      document.fonts.load('500 26px Caveat'), document.fonts.load('100px "Noto Music"', '\u{1D11E}\u{1D122}')]),
    new Promise(r => setTimeout(r, 2500))
  ]);

  let rig;
  try { rig = await loadModel(renderer); }      // CC0 baby grand (cleaned + compressed), see credits
  catch (err) { console.warn('model failed, using built-in piano', err); rig = proceduralRig(renderer); }
  const { piano, bookLook, bookCam, sheetsLook, sheetsCam } = rig;
  scene.add(piano);
  canvas.classList.add('ready');   // fade the scene in once the model is ready
  piano.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });

  let distF = 1, needs = true;
  const hemi = scene.children.find(o => o.isHemisphereLight);
  onThemeChange = (dark) => {
    spot.intensity = dark ? 95 : 0;          // stage light on
    beam.visible = dark;
    key.intensity = dark ? 0.0 : 1.6;        // daylight off
    key.castShadow = !dark;
    fill.intensity = dark ? 0.06 : 0.45;
    hemi.intensity = dark ? 0.04 : 0.55;
    rim.intensity = dark ? 0.35 : 0.0;
    roomMat.color.set(dark ? 0x0b0b0c : 0xf1f2ef);   // white room by day, black room under the stage light
    // softer reflections so the lacquered lid doesn't turn silver when seen from above
    piano.traverse(o => { if (o.isMesh && o.material && 'envMapIntensity' in o.material && o.material !== roomMat) o.material.envMapIntensity = dark ? 0.12 : 0.45; });
    // paper under the stage light: dim it so the ink stays readable instead of glowing white
    piano.traverse(o => { const t = o.isMesh && o.material && o.material.userData.tint;
      if (t) o.material.color.copy(t).multiplyScalar(dark ? 0.5 : 1); });
    needs = true;
  };
  syncTheme();

  /* camera keyframes, one per chapter */
  const V = (x, y, z) => new THREE.Vector3(x, y, z);
  const K = [
    { rot: -0.75, look: () => V(0, 0.7, 0), cam: () => V(3.7, 2.1, 4.4) },              // hero
    { rot: 1.25,  look: () => V(0, 0.7, 0), cam: () => V(3.0, 3.0, 4.5) },              // stages: piano turns to show its curve
    { rot: 0.0,   look: bookLook,   cam: bookCam },     // lesson notes: book on the stand
    { rot: 0.12,  look: sheetsLook, cam: sheetsCam },   // practice log: loose pages beside it
    { rot: 2.7,   look: () => V(0, 0.6, 0), cam: () => V(-3.4, 5.4, 2.4) },               // card: top-down
    { rot: Math.PI * 2 - 0.75, look: () => V(0, 0.7, 0), cam: () => V(3.7, 2.1, 4.4) }  // CTA: full circle back
  ];

  function resize() {
    const w = innerWidth, h = innerHeight;
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    if (w >= 1024) camera.setViewOffset(w, h, -w * 0.18, 0, w, h); // piano sits right of the text
    else camera.setViewOffset(w, h, 0, h * 0.2, w, h);             // piano sits above the text card
    camera.updateProjectionMatrix();
    distF = camera.aspect < 1 ? Math.min(2.6, 1.0 / camera.aspect + 0.2) : 1;
    computeAnchors();
    needs = true;
  }
  addEventListener('resize', resize);
  resize();

  const ease = (f) => { const x = Math.min(1, Math.max(0, (f - 0.15) / 0.7)); return x * x * (3 - 2 * x); };
  const desCam = new THREE.Vector3(), desLook = new THREE.Vector3(), tmp = new THREE.Vector3();
  const curCam = K[0].cam(), curLook = K[0].look();
  let curRot = K[0].rot, last = performance.now();

  function frame(now) {
    requestAnimationFrame(frame);        // schedule first, so one bad frame can't stop the loop
    try { step(now); } catch (e) { diag.err = String(e && e.message || e); }
  }
  function step(now) {
    const dt = Math.min((now - last) / 1000, 0.05); last = now;
    const reduce = !motionOn();
    const t = reduce ? 0 : scrollT();     // motion off: the piano stays still in its opening pose
    const i = Math.min(Math.floor(t), K.length - 1), f = t - i;
    const a = K[i], b = K[Math.min(i + 1, K.length - 1)], e = ease(f);
    const k = reduce ? 1 : 1 - Math.exp(-dt * 5);

    const desRot = a.rot + (b.rot - a.rot) * e;
    curRot += (desRot - curRot) * k;
    piano.rotation.y = curRot;
    piano.updateMatrixWorld(true);

    desLook.copy(a.look()).lerp(b.look(), e);
    desCam.copy(a.cam()).lerp(b.cam(), e);
    tmp.subVectors(desCam, desLook).multiplyScalar(distF);
    desCam.copy(desLook).add(tmp);
    curCam.lerp(desCam, k); curLook.lerp(desLook, k);

    const moving = curCam.distanceToSquared(desCam) > 1e-7 || curLook.distanceToSquared(desLook) > 1e-7 || Math.abs(desRot - curRot) > 1e-5;
    if (moving || needs) {               // only draw while something changes (saves battery)
      camera.position.copy(curCam);
      camera.lookAt(curLook);
      renderer.render(scene, camera);
      needs = false;
      diag.renders++;
    }
    diag.cam = curCam;
  }
  requestAnimationFrame(frame);
}

/* ---------- loaded model: CC0 "Baby Grand Piano" by Roy_1508348 (Blend Swap), logo removed ---------- */
async function loadModel(renderer) {
  const loader = new GLTFLoader().setMeshoptDecoder(MeshoptDecoder);
  const gltf = await loader.loadAsync(document.getElementById('scene').dataset.model);   // URL from the template (url_for)
  const piano = new THREE.Group();
  const model = gltf.scene;
  model.position.x = -0.18;                  // centre the keyboard on the rotation axis
  piano.add(model);
  const find = (label) => { let hit = null; const key = label.replace(/[ _]/g, '').toLowerCase();
    model.traverse(o => { if (!hit && o.name.replace(/[ _]/g, '').toLowerCase() === key) hit = o; }); return hit; };
  const mats = paperMaterials(renderer);
  const skin = (label, mat) => { const o = find(label); if (o) o.traverse(m => { if (m.isMesh) m.material = mat; }); return o; };
  const left = skin('Book Left Page', mats.bookLeft), right = skin('Book Right Page', mats.bookRight);
  skin('Loose Page 1', mats.music); skin('Loose Page 2', mats.music);
  const log = skin('Loose Page 3', mats.log);

  const centre = (o) => new THREE.Box3().setFromObject(o).getCenter(new THREE.Vector3());
  const front = () => new THREE.Vector3(0, 0, 1).applyQuaternion(piano.quaternion);
  // page normal from three of its corners in world space (robust to compressed/quantized meshes),
  // turned so it faces up-and-toward the player
  const normalOf = (o) => { const n = new THREE.Vector3();
    o.traverse(m => { if (!m.isMesh) return;
      const p = m.geometry.attributes.position, v = [0, 1, 2].map(i => new THREE.Vector3().fromBufferAttribute(p, i).applyMatrix4(m.matrixWorld));
      n.crossVectors(v[1].clone().sub(v[0]), v[2].clone().sub(v[0])).normalize(); });
    if (n.dot(front().add(new THREE.Vector3(0, 1, 0))) < 0) n.negate();
    return n; };
  return {
    piano,
    bookLook: () => centre(left).add(centre(right)).multiplyScalar(0.5),
    bookCam:  () => centre(left).add(centre(right)).multiplyScalar(0.5).add(normalOf(left).multiplyScalar(0.72)),
    sheetsLook: () => centre(log),
    sheetsCam:  () => centre(log).add(normalOf(log).multiplyScalar(0.5)).add(front().multiplyScalar(0.27))
  };
}
function proceduralRig(renderer) {
  const { piano, bookAnchor, sheetsAnchor } = buildPiano(renderer);
  const wp = (o) => o.getWorldPosition(new THREE.Vector3());
  const wd = (o) => o.getWorldDirection(new THREE.Vector3());
  return { piano,
    bookLook: () => wp(bookAnchor), bookCam: () => wp(bookAnchor).add(wd(bookAnchor).multiplyScalar(0.9)),
    sheetsLook: () => wp(sheetsAnchor), sheetsCam: () => wp(sheetsAnchor).add(wd(sheetsAnchor).multiplyScalar(0.72)) };
}

/* ---------- paper textures drawn on <canvas>: engraved sheet music + handwritten/printed notes ---------- */
let _paper;
function paperMaterials(renderer) {
  if (_paper) return _paper;
  const aniso = renderer.capabilities.getMaxAnisotropy();
  const PW = 1024, PH = 1400;                              // page ratio of the book and loose sheets
  const ML = 128, MR = PW - 108, MB = PH - 110;            // page margins: nothing is drawn outside these
  const INK = '#18181c', PENCIL = 'rgba(64,64,72,0.9)', TEAL = '#0E6F68';
  const MUSIC = '"Noto Music", "Bravura", "Segoe UI Symbol", serif';
  const SERIF = 'Newsreader, Georgia, serif', SANS = '"Atkinson Hyperlegible Next", system-ui, sans-serif', HAND = 'Caveat, "Segoe Print", cursive';

  // tint < 0xffffff darkens a sheet (the loose pages sit right under the stage light)
  function paper(draw, tint = 0xffffff) {
    const c = document.createElement('canvas'); c.width = PW; c.height = PH;
    const g = c.getContext('2d');
    g.fillStyle = '#F7F3EA'; g.fillRect(0, 0, PW, PH);
    g.fillStyle = INK; g.strokeStyle = INK; g.lineCap = 'round';
    draw(g);
    const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = aniso; t.flipY = false;
    const mat = new THREE.MeshStandardMaterial({ map: t, color: tint, roughness: 1, side: THREE.DoubleSide });
    mat.userData.tint = new THREE.Color(tint);               // syncTheme() dims it in dark mode
    return mat;
  }
  function seeded(seed) { let s = seed; return () => (s = (s * 16807) % 2147483647) / 2147483647; }
  const line = (g, x1, y1, x2, y2, w = 1.3) => { g.lineWidth = w; g.beginPath(); g.moveTo(x1, y1); g.lineTo(x2, y2); g.stroke(); };
  const text = (g, s, x, y, font, align = 'left', color = INK) => { g.font = font; g.textAlign = align; g.fillStyle = color; g.fillText(s, x, y); g.fillStyle = INK; };

  // a music symbol from the font, scaled so its ink fills `height` and starts at `top`
  function glyph(g, ch, x, top, height) {
    g.font = `100px ${MUSIC}`; g.textAlign = 'left';
    const m = g.measureText(ch), h = m.actualBoundingBoxAscent + m.actualBoundingBoxDescent;
    if (!h) return;
    const s = height / h;
    g.save(); g.translate(x, top + m.actualBoundingBoxAscent * s); g.scale(s, s); g.fillText(ch, 0, 0); g.restore();
  }
  function flat(g, x, y, sp) {                               // drawn by hand so it never depends on a font
    line(g, x, y - sp * 1.8, x, y + sp * 0.45, 1.6);
    g.lineWidth = 1.8; g.beginPath(); g.moveTo(x, y + sp * 0.45);
    g.bezierCurveTo(x + sp * 0.9, y - sp * 0.05, x + sp * 0.7, y - sp * 0.75, x, y - sp * 0.2); g.stroke();
  }
  function head(g, x, y, sp, filled) {
    g.save(); g.translate(x, y); g.rotate(-0.35); g.beginPath(); g.ellipse(0, 0, sp * 0.62, sp * 0.43, 0, 0, Math.PI * 2);
    if (filled) g.fill(); else { g.lineWidth = 1.7; g.stroke(); }
    g.restore();
  }
  function ledgers(g, x, p, bottom, sp) {
    for (let q = 10; q <= p; q += 2) line(g, x - sp, bottom - q * sp / 2, x + sp, bottom - q * sp / 2, 1.3);
    for (let q = -2; q >= p; q -= 2) line(g, x - sp, bottom - q * sp / 2, x + sp, bottom - q * sp / 2, 1.3);
  }
  // notes at xs / staff positions ps (0 = bottom line, 8 = top line), beamed together
  function beamed(g, xs, ps, bottom, sp, small = false) {
    const k = small ? 0.65 : 1, s = sp * k;
    const ys = ps.map(p => bottom - p * sp / 2);
    const up = ps.reduce((a, b) => a + b, 0) / ps.length < 4;
    xs.forEach((x, i) => { head(g, x, ys[i], s, true); ledgers(g, x, ps[i], bottom, sp); });
    const sx = xs.map(x => up ? x + s * 0.58 : x - s * 0.58);
    const by = up ? Math.min(...ys) - sp * 3.2 * k : Math.max(...ys) + sp * 3.2 * k;
    sx.forEach((x, i) => line(g, x, ys[i] + (up ? -s * 0.15 : s * 0.15), x, by, 1.5));
    const th = sp * 0.45 * k;
    g.beginPath(); g.moveTo(sx[0], up ? by : by - th); g.lineTo(sx[sx.length - 1], up ? by : by - th);
    g.lineTo(sx[sx.length - 1], up ? by + th : by); g.lineTo(sx[0], up ? by + th : by); g.closePath(); g.fill();
    return { up, top: Math.min(...ys, by), bottom: Math.max(...ys, by) };
  }
  function single(g, x, p, bottom, sp, { filled = true, dot = false } = {}) {
    const y = bottom - p * sp / 2, up = p < 4;
    head(g, x, y, sp, filled); ledgers(g, x, p, bottom, sp);
    const sx = up ? x + sp * 0.58 : x - sp * 0.58;
    line(g, sx, y, sx, up ? y - sp * 3.4 : y + sp * 3.4, 1.5);
    if (dot) { g.beginPath(); g.arc(x + sp * 1.15, p % 2 === 0 ? y - sp / 2 : y, sp * 0.17, 0, Math.PI * 2); g.fill(); }
    return { up, top: Math.min(y, up ? y - sp * 3.4 : y), bottom: Math.max(y, up ? y : y + sp * 3.4) };
  }
  function brace(g, x, top, bottom) {
    const mid = (top + bottom) / 2, w = 12;
    g.beginPath(); g.moveTo(x, top);
    g.bezierCurveTo(x - w * 1.6, top + 25, x + w * 0.6, mid - 25, x - w, mid);
    g.bezierCurveTo(x + w * 0.6, mid + 25, x - w * 1.6, bottom - 25, x, bottom);
    g.bezierCurveTo(x - w * 0.9, bottom - 25, x + w * 1.4, mid + 25, x - w * 0.6, mid);
    g.bezierCurveTo(x + w * 1.4, mid - 25, x - w * 0.9, top + 25, x, top); g.fill();
  }

  /* Engrave systems of a grand staff. Returns note positions so pencil marks can point at them. */
  function engrave(g, o) {
    const sp = 9, rnd = seeded(o.seed), x0 = ML, x1 = MR;
    const flatsT = [4, 7, 3].slice(0, o.flats), flatsB = [2, 5, 1].slice(0, o.flats);
    let m = o.firstMeasure, y = o.top;
    const notes = [];
    o.systems.forEach((count, si) => {
      const tTop = y, tBot = tTop + 4 * sp, bTop = tBot + 62, bBot = bTop + 4 * sp;
      for (let i = 0; i < 5; i++) { line(g, x0, tTop + i * sp, x1, tTop + i * sp, 1.2); line(g, x0, bTop + i * sp, x1, bTop + i * sp, 1.2); }
      brace(g, x0 - 10, tTop, bBot); line(g, x0, tTop, x0, bBot, 1.6);
      glyph(g, '\u{1D11E}', x0 + 6, tTop - sp * 1.7, sp * 7.3);       // treble clef
      glyph(g, '\u{1D122}', x0 + 6, bTop - sp * 0.1, sp * 3.3);       // bass clef
      let hx = x0 + sp * 4.3;
      flatsT.forEach((p, i) => flat(g, hx + i * sp * 1.15, tBot - p * sp / 2, sp));
      flatsB.forEach((p, i) => flat(g, hx + i * sp * 1.15, bBot - p * sp / 2, sp));
      hx += o.flats * sp * 1.15 + sp * 0.8;
      if (si === 0) {                                               // time signature on the first system only
        g.textBaseline = 'middle';
        for (const [top] of [[tTop], [bTop]]) {
          text(g, o.time[0], hx + sp, top + sp, `700 ${sp * 2.3}px Georgia, serif`, 'center');
          text(g, o.time[1], hx + sp, top + sp * 3, `700 ${sp * 2.3}px Georgia, serif`, 'center');
        }
        g.textBaseline = 'alphabetic'; hx += sp * 3;
      } else {
        text(g, String(m), x0, tTop - sp * 1.6, `italic 17px ${SERIF}`);  // measure number
      }
      const mw = (x1 - hx - sp) / count;
      for (let k = 0; k < count; k++, m++) {
        const mx = hx + sp + k * mw, groups = o.groups, gw = mw / groups;
        const sysNotes = [];
        let cur = 5 + Math.floor(rnd() * 3);
        const senza = o.senza === m;
        if (senza) {                                                // a free run of small notes ("senza tempo")
          const n = 22, xs = [], ps = [];
          for (let i = 0; i < n; i++) { cur = Math.max(2, Math.min(12, cur + (rnd() < 0.5 ? 1 : -1) * (1 + (rnd() < 0.3)))); xs.push(mx + 10 + i * (mw - 24) / n); ps.push(cur); }
          for (let i = 0; i < n; i += 6) beamed(g, xs.slice(i, i + 6), ps.slice(i, i + 6), tBot, sp, true);
          text(g, 'senza tempo', mx + 4, tTop - sp * 3.2, `italic 18px ${SERIF}`);
        }
        for (let gi = 0; gi < groups; gi++) {
          const gx = mx + gi * gw + sp * 0.9, step = (gw - sp * 1.8) / o.per;
          if (!senza) {                                             // right hand: melody
            const r = rnd();
            if (r < 0.5) {
              const xs = [], ps = [];
              for (let i = 0; i < o.per; i++) { cur = Math.max(2, Math.min(11, cur + Math.round((rnd() - 0.5) * 3))); xs.push(gx + i * step); ps.push(cur); }
              beamed(g, xs, ps, tBot, sp); xs.forEach((x, i) => sysNotes.push([x, tBot - ps[i] * sp / 2]));
            } else {
              cur = Math.max(3, Math.min(10, cur + Math.round((rnd() - 0.5) * 4)));
              single(g, gx, cur, tBot, sp, { filled: r < 0.8, dot: o.per === 3 }); sysNotes.push([gx, tBot - cur * sp / 2]);
            }
          }
          // left hand: bass note + chord tones (nocturne waltz pattern / Alberti bass)
          const base = [-1, 0, 1, 2][Math.floor(rnd() * 4)];
          const pat = o.per === 3 ? [base, base + 5, base + 7] : [base, base + 4, base + 2, base + 4];
          beamed(g, pat.map((_, i) => gx + i * step), pat, bBot, sp);
        }
        line(g, mx + mw - sp * 0.2, tTop, mx + mw - sp * 0.2, bBot, 1.4);         // barline through both staves
        if (m === o.finalAt) { line(g, mx + mw - sp * 0.8, tTop, mx + mw - sp * 0.8, bBot, 1.4); line(g, mx + mw, tTop, mx + mw, bBot, 4.5); }
        if (rnd() < 0.55) {                                         // slur over the right hand
          const sx = mx + sp, ex = mx + mw - sp * 1.6, sy = tTop - sp * 3.6;
          g.lineWidth = 1.3; g.beginPath(); g.moveTo(sx, sy + 6); g.quadraticCurveTo((sx + ex) / 2, sy - 10, ex, sy + 6); g.stroke();
        }
        if (rnd() < 0.45) { text(g, 'Ped.', mx + 4, bBot + sp * 5.2, `italic 700 17px ${SERIF}`); text(g, '*', mx + mw - sp * 2.5, bBot + sp * 5.2, `700 20px ${SERIF}`); }
        notes.push({ measure: m, system: si, x: mx, w: mw, tTop, bBot, rh: sysNotes });
      }
      const dyn = o.dynamics && o.dynamics[si];
      if (dyn) text(g, dyn, hx + sp, tBot + 34, `italic 700 22px ${SERIF}`);
      y += o.systemGap;
    });
    return notes;
  }
  function wrap(g, s, x, y, maxW, lh) {
    const words = s.split(' '); let ln = '';
    for (const w of words) { const t = ln ? ln + ' ' + w : w; if (g.measureText(t).width > maxW && ln) { g.fillText(ln, x, y); y += lh; ln = w; } else ln = t; }
    if (ln) g.fillText(ln, x, y);
    return y + lh;
  }

  /* --- book, left page: first page of the Nocturne, with the teacher's pencil marks --- */
  const bookLeft = paper((g) => {
    text(g, 'Nocturne', PW / 2, 118, `500 60px ${SERIF}`, 'center');
    text(g, 'in E♭ major, Op. 9 No. 2', PW / 2, 162, `400 28px ${SERIF}`, 'center');
    text(g, 'Frédéric Chopin', MR, 208, `400 24px ${SERIF}`, 'right');
    text(g, 'Andante', ML, 246, `700 24px ${SERIF}`);
    const ms = engrave(g, { seed: 7, flats: 3, time: ['12', '8'], groups: 4, per: 3, firstMeasure: 1, top: 296, systemGap: 172,
      systems: [3, 3, 3, 3, 3, 3], dynamics: ['p  espress. dolce', null, 'cresc.', null, 'p', null] });
    text(g, '1', PW / 2, PH - 56, `400 20px ${SERIF}`, 'center');
    // pencil marks: fingering, a circled bar, a bracket over mm. 12–18, the lesson date
    g.font = `500 26px ${HAND}`; g.fillStyle = PENCIL; g.textAlign = 'left';
    ms[0].rh.slice(0, 4).forEach(([x, y], i) => g.fillText(['1', '2', '4', '3'][i], x - 6, y - 52));
    const c = ms[4]; g.strokeStyle = PENCIL; g.lineWidth = 2.2;
    g.beginPath(); g.ellipse(c.x + c.w / 2, c.tTop + 18, c.w / 2 + 8, 52, -0.05, 0, Math.PI * 2); g.stroke();
    g.fillText('even, then shape', c.x + c.w + 14, c.tTop - 36);
    const a = ms.find(n => n.measure === 13), end = ms.filter(n => n.system === a.system).pop();
    const by = a.bBot + 18;                                    // bracket under the left hand, arrow = "keeps going"
    line(g, a.x + 6, by - 10, a.x + 6, by, 2.2); line(g, a.x + 6, by, end.x + end.w - 10, by, 2.2);
    line(g, end.x + end.w - 24, by - 8, end.x + end.w - 10, by, 2.2); line(g, end.x + end.w - 24, by + 8, end.x + end.w - 10, by, 2.2);
    g.fillText('slow LH!  mm. 12–24  →', a.x + 14, by + 28);
    g.fillStyle = TEAL; g.font = `600 30px ${HAND}`;
    g.fillText('Nov 16 — stage 3 ✓   next: stage 4', ML, 70);
    g.fillStyle = INK; g.strokeStyle = INK;
  });
  /* --- book, right page: the rest of the Nocturne (mm. 19–34) --- */
  const bookRight = paper((g) => {
    text(g, 'Op. 9 No. 2', ML, 70, `italic 400 22px ${SERIF}`);
    text(g, '2', MR, 70, `400 22px ${SERIF}`, 'right');
    const ms = engrave(g, { seed: 19, flats: 3, time: ['12', '8'], groups: 4, per: 3, firstMeasure: 19, top: 120, systemGap: 182,
      systems: [3, 3, 3, 3, 2, 2], senza: 33, finalAt: 34, dynamics: [null, 'cresc.', 'f', 'dim.', null, 'pp'] });
    g.font = `500 26px ${HAND}`; g.fillStyle = PENCIL;
    const s = ms.find(n => n.measure === 33); if (s) g.fillText('chunk it — free, not fast', s.x + 6, s.bBot + 78);
    g.fillStyle = INK;
  });

  /* --- loose sheets: Clementi underneath, the student's practice notes on top --- */
  const music = paper((g) => {
    text(g, 'Sonatina', PW / 2, 118, `500 58px ${SERIF}`, 'center');
    text(g, 'in C major, Op. 36 No. 1', PW / 2, 160, `400 28px ${SERIF}`, 'center');
    text(g, 'Muzio Clementi', MR, 206, `400 24px ${SERIF}`, 'right');
    text(g, 'Spiritoso', ML, 246, `700 24px ${SERIF}`);
    engrave(g, { seed: 3, flats: 0, time: ['2', '2'], groups: 2, per: 4, firstMeasure: 1, top: 296, systemGap: 172,
      systems: [4, 4, 4, 4, 4, 4], dynamics: ['f', null, 'p', null, 'f', null] });
  }, 0xcfc9bc);
  const log = paper((g) => {
    const L = ML, R = MR, W = R - L;
    text(g, 'Practice notes', L, 112, `500 50px ${SERIF}`, 'left', '#1F3B63');
    text(g, 'Nocturne in E♭ major, Op. 9 No. 2 (Chopin)  ·  week of Nov 16', L, 156, `400 24px ${SANS}`, 'left', '#4B5A6B');
    g.fillStyle = TEAL; g.fillRect(L, 176, 70, 5); g.fillStyle = INK;
    const rows = [
      ['mm. 1–4', 'Slow practice: sing the melody, then play the right hand alone at ♪ = 80.'],
      ['mm. 5–8', 'Left hand alone: bass note, then the chord. Eyes on the score, not on the hands.'],
      ['mm. 9–12', 'Rhythm variations on the fast right-hand notes: long–short, then short–long.'],
      ['mm. 12–24', 'Slow left hand (teacher’s note). Hands together only at ♪ = 88; raise the metronome 4 clicks a day.'],
      ['mm. 16–20', 'Chunking: groups of 4 notes, then join them. Start at m. 20 and work backward.'],
      ['mm. 21–24', 'Pedal: change on beats 1 and 4 and listen for a clean bass.'],
      ['m. 33', 'Senza tempo run: practice it in chunks. It is free time, not fast.'],
      ['Ornaments', 'Play them as even notes first, then fit them into the beat.'],
      ['Every day', 'Record one run at the end; mark 2 spots to start with tomorrow.']
    ];
    let y = 236;
    for (const [mm, tip] of rows) {
      text(g, mm, L, y, `700 24px ${SANS}`, 'left', TEAL);
      g.font = `400 24px ${SANS}`; g.fillStyle = INK; g.textAlign = 'left';
      y = wrap(g, tip, L + 178, y, W - 178, 32) + 14;
    }
    y += 10; line(g, L, y, R, y, 1.2); y += 44;
    text(g, 'This week', L, y, `700 24px ${SANS}`, 'left', '#1F3B63');
    const days = [['Mo', 30], ['Tu', 0], ['We', 25], ['Th', 30], ['Fr', 15], ['Sa', 45], ['Su', 0]];
    days.forEach(([d, mins], i) => { const x = L + 150 + i * 80; text(g, d, x, y, `700 22px ${SANS}`, 'left', '#4B5A6B'); text(g, mins ? mins + '' : '–', x, y + 32, `400 22px ${SANS}`); });
    text(g, '= 145 min', R, y + 76, `700 24px ${SANS}`, 'right', TEAL);
    text(g, '“pedal much cleaner today”', L, Math.min(y + 124, MB), `500 32px ${HAND}`, 'left', PENCIL);
  }, 0xd6d1c5);
  _paper = { bookLeft, bookRight, log, music };
  return _paper;
}

/* ---------- fallback: procedural grand piano ---------- */
function buildPiano(renderer) {
  const piano = new THREE.Group();
  const inner = new THREE.Group();
  inner.position.z = 0.95;               // centre the body on the rotation axis
  piano.add(inner);

  const lacquer = new THREE.MeshPhysicalMaterial({ color: 0x0c1422, roughness: 0.3, clearcoat: 1, clearcoatRoughness: 0.08 });
  const plate = new THREE.MeshStandardMaterial({ color: 0xb8925a, metalness: 0.6, roughness: 0.45 });
  const brass = new THREE.MeshStandardMaterial({ color: 0xc4a265, metalness: 0.9, roughness: 0.3 });
  const ivory = new THREE.MeshStandardMaterial({ color: 0xf2f0ea, roughness: 0.35 });
  const ebony = new THREE.MeshStandardMaterial({ color: 0x111418, roughness: 0.4 });
  const paperPlain = new THREE.MeshStandardMaterial({ color: 0xF4F0E6, roughness: 0.9 });

  const W = 1.5, half = W / 2, LEG = 0.66, CASE_H = 0.32, TOP = LEG + CASE_H;

  // outline (x = width, y = depth toward the tail)
  function outline(front = 0) {
    const s = new THREE.Shape();
    s.moveTo(-half, front);
    s.lineTo(half, front);
    s.lineTo(half, Math.max(front, 0.45));
    s.bezierCurveTo(half, 0.95, 0.05, 1.05, 0.0, 1.55);
    s.bezierCurveTo(-0.05, 2.0, -0.35, 2.25, -0.55, 2.25);
    s.bezierCurveTo(-0.72, 2.25, -half, 2.1, -half, 1.95);
    s.lineTo(-half, front);
    return s;
  }
  const caseGeo = new THREE.ExtrudeGeometry(outline(), { depth: CASE_H, bevelEnabled: true, bevelThickness: 0.01, bevelSize: 0.01, bevelSegments: 2, curveSegments: 48 });
  caseGeo.rotateX(-Math.PI / 2);          // shape depth -> -z, extrusion -> +y
  const body = new THREE.Mesh(caseGeo, [plate, lacquer]);  // caps show the gold plate, sides are lacquer
  body.position.y = LEG;
  inner.add(body);

  // lid, hinged on the straight (bass) side, front flap folded back
  const lidGeo = new THREE.ExtrudeGeometry(outline(0.38), { depth: 0.02, bevelEnabled: false, curveSegments: 48 });
  lidGeo.rotateX(-Math.PI / 2);
  lidGeo.translate(half, 0, 0);
  const lidPivot = new THREE.Group();
  lidPivot.position.set(-half, TOP + 0.01, 0);
  lidPivot.rotation.z = 0.5;
  lidPivot.add(new THREE.Mesh(lidGeo, lacquer));
  inner.add(lidPivot);
  const d = 1.25, a = 0.5;
  const prop = new THREE.Mesh(new THREE.CylinderGeometry(0.012, 0.012, d * Math.sin(a), 8), lacquer);
  prop.position.set(-half + d * Math.cos(a), TOP + d * Math.sin(a) / 2, -0.9);
  inner.add(prop);

  // keybed, cheeks, fallboard
  const box = (w, h, dd, mat, x, y, z) => { const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, dd), mat); m.position.set(x, y, z); inner.add(m); return m; };
  box(W, 0.1, 0.34, lacquer, 0, LEG - 0.05 + 0.04, 0.17);
  box(0.06, 0.18, 0.34, lacquer, -half + 0.03, LEG + 0.03, 0.17);
  box(0.06, 0.18, 0.34, lacquer, half - 0.03, LEG + 0.03, 0.17);
  box(W - 0.12, 0.08, 0.03, lacquer, 0, LEG + 0.1, 0.02);

  // keys: 52 white, 36 black (A0 to C8), instanced
  const kbW = W - 0.12, nW = 52, wkW = kbW / nW;
  const white = new THREE.InstancedMesh(new THREE.BoxGeometry(wkW * 0.92, 0.022, 0.27), ivory, nW);
  const blacks = [];
  const m4 = new THREE.Matrix4();
  for (let i = 0; i < nW; i++) {
    const x = -kbW / 2 + wkW * (i + 0.5);
    m4.makeTranslation(x, LEG + 0.1, 0.19);
    white.setMatrixAt(i, m4);
    const letter = 'ABCDEFG'[i % 7];
    if (i < nW - 1 && 'ACDFG'.includes(letter)) blacks.push(x + wkW / 2);
  }
  const black = new THREE.InstancedMesh(new THREE.BoxGeometry(wkW * 0.55, 0.03, 0.16), ebony, blacks.length);
  blacks.forEach((x, j) => { m4.makeTranslation(x, LEG + 0.125, 0.135); black.setMatrixAt(j, m4); });
  inner.add(white, black);

  // legs, casters, pedal lyre
  const legGeo = new THREE.CylinderGeometry(0.05, 0.035, LEG, 16);
  [[-0.62, -0.12], [0.62, -0.12], [-0.42, -1.9]].forEach(([x, z]) => {
    const leg = new THREE.Mesh(legGeo, lacquer); leg.position.set(x, LEG / 2, z); inner.add(leg);
    const c = new THREE.Mesh(new THREE.SphereGeometry(0.035, 12, 8), brass); c.position.set(x, 0.035, z); inner.add(c);
  });
  box(0.05, LEG - 0.12, 0.05, lacquer, -0.08, LEG / 2 + 0.06, -0.35);
  box(0.05, LEG - 0.12, 0.05, lacquer, 0.08, LEG / 2 + 0.06, -0.35);
  box(0.3, 0.05, 0.14, lacquer, 0, 0.1, -0.32);
  [-0.08, 0, 0.08].forEach(x => box(0.035, 0.012, 0.12, brass, x, 0.13, -0.2));

  // bench
  box(0.78, 0.06, 0.36, lacquer, 0, 0.5, 0.78);
  [[-0.34, 0.64], [0.34, 0.64], [-0.34, 0.92], [0.34, 0.92]].forEach(([x, z]) => box(0.04, 0.47, 0.04, lacquer, x, 0.235, z));

  // music desk (tilted back) with ledge
  const desk = new THREE.Group();
  desk.position.set(0, TOP + 0.005, -0.12);
  desk.rotation.x = -0.26;
  inner.add(desk);
  const satin = new THREE.MeshStandardMaterial({ color: 0x0c1422, roughness: 0.6 }); // matte desk: no glare behind the pages
  const board = new THREE.Mesh(new THREE.BoxGeometry(0.95, 0.31, 0.015), satin);
  board.position.set(0, 0.155, -0.008);
  desk.add(board);
  const ledge = new THREE.Mesh(new THREE.BoxGeometry(0.95, 0.02, 0.05), lacquer);
  ledge.position.set(0, 0.01, 0.02);
  desk.add(ledge);

  /* paper textures drawn on <canvas> */
  const aniso = renderer.capabilities.getMaxAnisotropy();
  function paper(draw) {
    const c = document.createElement('canvas'); c.width = 512; c.height = 700;
    const g = c.getContext('2d');
    g.fillStyle = '#F4F0E6'; g.fillRect(0, 0, c.width, c.height);
    draw(g, c);
    const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = aniso;
    return new THREE.MeshStandardMaterial({ map: t, roughness: 0.9 });
  }
  function staves(g, y0, count) {
    g.strokeStyle = 'rgba(19,34,56,.35)'; g.lineWidth = 1.5;
    for (let s = 0; s < count; s++) for (let l = 0; l < 5; l++) {
      const y = y0 + s * 80 + l * 9; g.beginPath(); g.moveTo(36, y); g.lineTo(476, y); g.stroke();
    }
    g.fillStyle = 'rgba(19,34,56,.75)';
    for (let s = 0; s < count; s++) for (let n = 0; n < 9; n++) {
      g.beginPath(); g.ellipse(70 + n * 46, y0 + s * 80 + ((n * 7 + s * 3) % 9) * 4.5, 6, 4.5, -0.4, 0, Math.PI * 2); g.fill();
    }
  }
  const inkFont = (w, s) => `${w} ${s}px "Atkinson Hyperlegible Next", system-ui, sans-serif`;
  const bookLeft = paper((g) => {
    g.fillStyle = '#1F3B63'; g.font = '500 44px Newsreader, Georgia, serif'; g.fillText('Lesson notes', 40, 84);
    g.fillStyle = '#4B5A6B'; g.font = inkFont(400, 22); g.fillText('Nov 16 · [Ms. Alvarez]', 40, 120);
    g.fillStyle = '#0E6F68'; g.fillRect(40, 138, 60, 4);
    g.fillStyle = '#132238'; g.font = 'italic 400 30px Newsreader, Georgia, serif';
    ['Slow left hand, mm. 12–24', 'Pedal changes on beat 1', 'Hands together at 72 bpm', 'Next week: aim for stage 4'].forEach((l, i) => g.fillText(l, 40, 210 + i * 64));
    staves(g, 500, 2);
  });
  const bookRight = paper((g) => { staves(g, 70, 7); });
  const sheetLog = paper((g) => {
    g.fillStyle = '#1F3B63'; g.font = '500 44px Newsreader, Georgia, serif'; g.fillText('Practice log', 40, 84);
    g.fillStyle = '#0E6F68'; g.fillRect(40, 104, 60, 4);
    g.font = inkFont(700, 26); g.fillStyle = '#132238';
    [['Mon', '30 min', 'Nocturne'], ['Wed', '25 min', 'Nocturne'], ['Thu', '30 min', 'Clementi'], ['Fri', '15 min', 'Nocturne'], ['Sat', '45 min', 'Nocturne']]
      .forEach(([d, m, p], i) => { const y = 170 + i * 56; g.fillText(d, 40, y); g.fillText(m, 130, y); g.font = inkFont(400, 26); g.fillText(p, 270, y); g.font = inkFont(700, 26); });
    g.fillStyle = '#4B5A6B'; g.font = 'italic 400 28px Newsreader, Georgia, serif';
    g.fillText('“m. 17 trill cleaner today”', 40, 500);
    g.fillStyle = '#0E6F68'; g.font = inkFont(700, 30); g.fillText('145 min this week', 40, 600);
  });
  const sheetMusic = paper((g) => staves(g, 70, 7));

  // open book (two leaves in a shallow V)
  const book = new THREE.Group();
  book.position.set(-0.14, 0.16, 0.012);
  desk.add(book);
  const leaf = (mat, side) => {
    const m = new THREE.Mesh(new THREE.BoxGeometry(0.21, 0.28, 0.008), [paperPlain, paperPlain, paperPlain, paperPlain, mat, paperPlain]);
    m.position.x = side * 0.106; m.rotation.y = -side * 0.07; book.add(m);
  };
  leaf(bookLeft, -1); leaf(bookRight, 1);
  const bookAnchor = new THREE.Object3D(); bookAnchor.position.set(-0.14, 0.15, 0); desk.add(bookAnchor);

  // loose pages beside the book
  const sheets = new THREE.Group();
  sheets.position.set(0.3, 0.15, 0.006);
  desk.add(sheets);
  [[sheetMusic, 0.07, 0.03, -0.004], [sheetMusic, -0.05, 0.015, -0.002], [sheetLog, 0.02, 0, 0]].forEach(([mat, rz, dx, dz]) => {
    const p = new THREE.Mesh(new THREE.PlaneGeometry(0.2, 0.27), mat);
    p.material.side = THREE.DoubleSide;
    p.rotation.z = rz; p.position.set(dx, 0, 0.004 + dz + 0.004);
    sheets.add(p);
  });
  const sheetsAnchor = new THREE.Object3D(); sheetsAnchor.position.set(0.3, 0.15, 0); desk.add(sheetsAnchor);

  return { piano, bookAnchor, sheetsAnchor };
}