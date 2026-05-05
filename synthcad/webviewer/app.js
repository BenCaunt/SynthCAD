import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

const elements = {
  canvas: document.querySelector('#viewerCanvas'),
  overlay: document.querySelector('#viewerOverlay'),
  targetSelect: document.querySelector('#targetSelect'),
  reloadTargetButton: document.querySelector('#reloadTargetButton'),
  fitAllButton: document.querySelector('#fitAllButton'),
  fitSelectionButton: document.querySelector('#fitSelectionButton'),
  isoViewButton: document.querySelector('#isoViewButton'),
  frontViewButton: document.querySelector('#frontViewButton'),
  rightViewButton: document.querySelector('#rightViewButton'),
  topViewButton: document.querySelector('#topViewButton'),
  orbitModeButton: document.querySelector('#orbitModeButton'),
  panModeButton: document.querySelector('#panModeButton'),
  partList: document.querySelector('#partList'),
  partCountBadge: document.querySelector('#partCountBadge'),
  partSearchInput: document.querySelector('#partSearchInput'),
  showAllPartsButton: document.querySelector('#showAllPartsButton'),
  isolateSelectedButton: document.querySelector('#isolateSelectedButton'),
  hideSelectedButton: document.querySelector('#hideSelectedButton'),
  targetStatusBadge: document.querySelector('#targetStatusBadge'),
  targetSummary: document.querySelector('#targetSummary'),
  selectionDetails: document.querySelector('#selectionDetails'),
  sectionAxisSelect: document.querySelector('#sectionAxisSelect'),
  sectionFlipCheckbox: document.querySelector('#sectionFlipCheckbox'),
  sectionSlider: document.querySelector('#sectionSlider'),
  sectionSliderLabel: document.querySelector('#sectionSliderLabel'),
  sectionReadout: document.querySelector('#sectionReadout'),
  interferenceCountBadge: document.querySelector('#interferenceCountBadge'),
  intentionalInterferenceList: document.querySelector('#intentionalInterferenceList'),
  interferenceList: document.querySelector('#interferenceList'),
  inspectionGallery: document.querySelector('#inspectionGallery'),
};

const loader = new GLTFLoader();
const raycaster = new THREE.Raycaster();
const pointer = new THREE.Vector2();
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x111827);

const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 10000);
camera.position.set(240, -240, 180);
camera.up.set(0, 0, 1);

const renderer = new THREE.WebGLRenderer({ canvas: elements.canvas, antialias: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.localClippingEnabled = true;

const controls = new OrbitControls(camera, elements.canvas);
controls.enableDamping = true;
controls.dampingFactor = 0.08;
controls.screenSpacePanning = true;
controls.mouseButtons.LEFT = THREE.MOUSE.ROTATE;
controls.mouseButtons.RIGHT = THREE.MOUSE.PAN;
controls.mouseButtons.MIDDLE = THREE.MOUSE.DOLLY;
controls.target.set(0, 0, 0);
controls.update();

const ambientLight = new THREE.AmbientLight(0xffffff, 0.85);
scene.add(ambientLight);

const hemiLight = new THREE.HemisphereLight(0xffffff, 0xcbd5e1, 1.35);
scene.add(hemiLight);

const keyLight = new THREE.DirectionalLight(0xffffff, 1.15);
keyLight.position.set(200, -280, 240);
scene.add(keyLight);

const fillLight = new THREE.DirectionalLight(0xffffff, 0.95);
fillLight.position.set(-220, 180, 160);
scene.add(fillLight);

const rimLight = new THREE.DirectionalLight(0xffffff, 0.55);
rimLight.position.set(-120, -140, 260);
scene.add(rimLight);

const state = {
  indexData: null,
  targetDetail: null,
  loadedScene: null,
  assemblyRoot: null,
  partGroups: [],
  partRows: [],
  partBoxes: [],
  childIndexByLabel: new Map(),
  meshes: [],
  hiddenParts: new Set(),
  selectedPartIndex: null,
  interferenceFocus: new Set(),
  interactionMode: 'orbit',
  modelBox: null,
  modelMetadataBboxMm: null,
  focusBox: null,
  activeLoadToken: null,
  sectionPlane: new THREE.Plane(new THREE.Vector3(1, 0, 0), 0),
  activeClippingPlanes: [],
};

function setOverlay(message) {
  elements.overlay.textContent = message;
  elements.overlay.classList.remove('hidden');
}

function clearOverlay() {
  elements.overlay.classList.add('hidden');
  elements.overlay.textContent = '';
}

function formatNumber(value, digits = 2) {
  if (typeof value !== 'number' || Number.isNaN(value)) {
    return '-';
  }
  return value.toFixed(digits);
}

function humanLabelFromUrl(url) {
  const base = url.split('/').pop() || url;
  return base.replace(/\.svg$/i, '').replace(/\.glb$/i, '').replace(/-/g, ' ');
}

function bboxToBox3(bbox) {
  if (!bbox || !Array.isArray(bbox.min) || !Array.isArray(bbox.max)) {
    return null;
  }
  return new THREE.Box3(
    new THREE.Vector3(...bbox.min),
    new THREE.Vector3(...bbox.max),
  );
}

function metadataBoxToSceneBox3(bboxMm) {
  const metadataBox = bboxToBox3(bboxMm);
  if (!metadataBox || !state.modelBox || !state.modelMetadataBboxMm) {
    return metadataBox;
  }

  const modelMetadataBox = bboxToBox3(state.modelMetadataBboxMm);
  if (!modelMetadataBox || modelMetadataBox.isEmpty() || state.modelBox.isEmpty()) {
    return metadataBox;
  }

  const mappedMin = new THREE.Vector3();
  const mappedMax = new THREE.Vector3();
  ['x', 'y', 'z'].forEach((axis, axisIndex) => {
    const metadataMin = modelMetadataBox.min.getComponent(axisIndex);
    const metadataSize = modelMetadataBox.max.getComponent(axisIndex) - metadataMin;
    const sceneMin = state.modelBox.min.getComponent(axisIndex);
    const sceneSize = state.modelBox.max.getComponent(axisIndex) - sceneMin;

    if (Math.abs(metadataSize) < 1e-9) {
      mappedMin.setComponent(axisIndex, sceneMin);
      mappedMax.setComponent(axisIndex, sceneMin + sceneSize);
      return;
    }

    const bboxMin = metadataBox.min.getComponent(axisIndex);
    const bboxMax = metadataBox.max.getComponent(axisIndex);
    const normalizedMin = (bboxMin - metadataMin) / metadataSize;
    const normalizedMax = (bboxMax - metadataMin) / metadataSize;
    mappedMin.setComponent(axisIndex, sceneMin + normalizedMin * sceneSize);
    mappedMax.setComponent(axisIndex, sceneMin + normalizedMax * sceneSize);
  });

  return new THREE.Box3(mappedMin, mappedMax);
}

function disposeObject3D(root) {
  if (!root) {
    return;
  }
  root.traverse((object) => {
    if (object.geometry) {
      object.geometry.dispose();
    }
    if (!object.material) {
      return;
    }
    const materials = Array.isArray(object.material) ? object.material : [object.material];
    materials.filter(Boolean).forEach((material) => material.dispose());
  });
}

function clearCurrentScene() {
  if (state.loadedScene) {
    scene.remove(state.loadedScene);
    disposeObject3D(state.loadedScene);
  }
  state.targetDetail = null;
  state.loadedScene = null;
  state.assemblyRoot = null;
  state.partGroups = [];
  state.partRows = [];
  state.partBoxes = [];
  state.childIndexByLabel = new Map();
  state.meshes = [];
  state.hiddenParts = new Set();
  state.selectedPartIndex = null;
  state.interferenceFocus = new Set();
  state.modelBox = null;
  state.modelMetadataBboxMm = null;
  state.focusBox = null;
}

function findTargetOverview(name) {
  return (state.indexData?.targets || []).find((target) => target.name === name) || null;
}

function renderOverviewOnly(overview, statusMessage = 'Loading target metadata…') {
  elements.targetStatusBadge.textContent = overview?.status || '-';
  elements.partCountBadge.textContent = '-';
  elements.interferenceCountBadge.textContent = String(overview?.interference_count || 0);
  elements.targetSummary.innerHTML = `
    <dt>Name</dt><dd>${overview?.name || '-'}</dd>
    <dt>Kind</dt><dd>${overview?.kind || '-'}</dd>
    <dt>Project</dt><dd>${overview?.project || '-'}</dd>
    <dt>Printable</dt><dd>${overview?.printable ? 'yes' : 'no'}</dd>
    <dt>Metadata</dt><dd>${statusMessage}</dd>
  `;
  elements.partList.className = 'part-list empty-state';
  elements.partList.textContent = statusMessage;
  elements.selectionDetails.textContent = 'No part selected.';
  elements.intentionalInterferenceList.innerHTML = '';
  elements.interferenceList.className = 'interference-list empty-state';
  elements.interferenceList.textContent = 'Waiting for target metadata…';
  elements.inspectionGallery.className = 'gallery empty-state';
  elements.inspectionGallery.textContent = 'Waiting for inspection metadata…';
}

function forEachMaterial(materialOrArray, callback) {
  const materials = Array.isArray(materialOrArray) ? materialOrArray : [materialOrArray];
  materials.filter(Boolean).forEach(callback);
}

function cloneMeshMaterials(mesh) {
  if (!mesh.material) {
    return;
  }
  if (Array.isArray(mesh.material)) {
    mesh.material = mesh.material.map((material) => material.clone());
  } else {
    mesh.material = mesh.material.clone();
  }
  forEachMaterial(mesh.material, (material) => {
    material.userData.viewerBase = {
      color: material.color ? material.color.clone() : null,
      emissive: material.emissive ? material.emissive.clone() : null,
      opacity: material.opacity,
      transparent: material.transparent,
      clippingPlanes: [],
    };
  });
}

function pickAssemblyRoot(gltfScene, expectedPartCount) {
  if (!gltfScene) {
    return null;
  }
  const candidates = [gltfScene];
  gltfScene.traverse((object) => {
    if (object !== gltfScene && object.children.length > 0) {
      candidates.push(object);
    }
  });

  const exact = candidates.find((object) => object.children.length === expectedPartCount);
  if (exact) {
    return exact;
  }

  if (gltfScene.children.length === 1) {
    return gltfScene.children[0];
  }

  return gltfScene;
}

function buildChildIndexByLabel(children) {
  const map = new Map();
  children.forEach((child) => {
    const key = child.label.toLowerCase();
    const bucket = map.get(key) || [];
    bucket.push(child.index);
    map.set(key, bucket);
  });
  return map;
}

function partIndicesForLabel(label) {
  return state.childIndexByLabel.get(String(label || '').toLowerCase()) || [];
}

function resetMaterialAppearance() {
  state.meshes.forEach((mesh) => {
    forEachMaterial(mesh.material, (material) => {
      const base = material.userData.viewerBase;
      if (!base) {
        return;
      }
      if (base.color && material.color) {
        material.color.copy(base.color);
      }
      if (base.emissive && material.emissive) {
        material.emissive.copy(base.emissive);
        material.emissiveIntensity = 1;
      }
      material.opacity = base.opacity;
      material.transparent = base.transparent;
      material.needsUpdate = true;
    });
  });
}

function applyHighlightToPart(partIndex, kind) {
  const part = state.partGroups[partIndex];
  if (!part) {
    return;
  }
  part.traverse((object) => {
    if (!object.isMesh) {
      return;
    }
    forEachMaterial(object.material, (material) => {
      if (kind === 'selected') {
        if (material.emissive) {
          material.emissive.setRGB(0.85, 0.65, 0.05);
          material.emissiveIntensity = 1.6;
        } else if (material.color) {
          material.color.offsetHSL(0.02, 0.08, 0.18);
        }
      }
      if (kind === 'interference') {
        if (material.emissive) {
          material.emissive.setRGB(0.88, 0.15, 0.15);
          material.emissiveIntensity = 1.8;
        } else if (material.color) {
          material.color.setRGB(0.93, 0.3, 0.28);
        }
      }
    });
  });
}

function updatePartVisuals() {
  state.partGroups.forEach((group, index) => {
    if (!group) {
      return;
    }
    group.visible = !state.hiddenParts.has(index);
  });

  resetMaterialAppearance();
  state.interferenceFocus.forEach((partIndex) => applyHighlightToPart(partIndex, 'interference'));
  if (Number.isInteger(state.selectedPartIndex)) {
    applyHighlightToPart(state.selectedPartIndex, 'selected');
  }

  state.partRows.forEach((row, index) => {
    row.classList.toggle('selected', index === state.selectedPartIndex);
    row.classList.toggle('hidden-part', state.hiddenParts.has(index));
    const toggle = row.querySelector('input[type="checkbox"]');
    if (toggle) {
      toggle.checked = !state.hiddenParts.has(index);
    }
  });
}

function applyClippingPlanes() {
  state.meshes.forEach((mesh) => {
    forEachMaterial(mesh.material, (material) => {
      material.clippingPlanes = state.activeClippingPlanes;
      material.clipShadows = true;
      material.needsUpdate = true;
    });
  });
}

function fitCameraToBox(box) {
  if (!box || box.isEmpty()) {
    return;
  }
  const size = box.getSize(new THREE.Vector3());
  const center = box.getCenter(new THREE.Vector3());
  const maxSize = Math.max(size.x, size.y, size.z, 1);
  const fov = THREE.MathUtils.degToRad(camera.fov);
  let distance = (maxSize / 2) / Math.tan(fov / 2);
  distance *= 1.85;

  let direction = camera.position.clone().sub(controls.target);
  if (direction.lengthSq() < 1e-6) {
    direction = new THREE.Vector3(1, -1, 0.75);
  }
  direction.normalize();

  camera.position.copy(center.clone().add(direction.multiplyScalar(distance)));
  controls.target.copy(center);
  camera.near = Math.max(distance / 100, 0.1);
  camera.far = Math.max(distance * 20, 1000);
  camera.updateProjectionMatrix();
  controls.update();
}

function currentFocusBox() {
  if (state.focusBox && !state.focusBox.isEmpty()) {
    return state.focusBox;
  }
  return state.modelBox;
}

function setPresetView(direction, up = new THREE.Vector3(0, 0, 1)) {
  const box = currentFocusBox();
  if (!box || box.isEmpty()) {
    return;
  }
  const size = box.getSize(new THREE.Vector3());
  const center = box.getCenter(new THREE.Vector3());
  const radius = Math.max(size.x, size.y, size.z, 1) * 1.7;
  const viewDirection = direction.clone().normalize();
  camera.up.copy(up);
  camera.position.copy(center.clone().add(viewDirection.multiplyScalar(radius)));
  controls.target.copy(center);
  camera.near = Math.max(radius / 100, 0.1);
  camera.far = Math.max(radius * 20, 1000);
  camera.updateProjectionMatrix();
  controls.update();
}

function updateSelectionDetails() {
  const detail = state.targetDetail;
  if (!detail) {
    elements.selectionDetails.textContent = 'No target loaded.';
    return;
  }

  if (!Number.isInteger(state.selectedPartIndex)) {
    elements.selectionDetails.textContent = 'No part selected.';
    return;
  }

  const child = detail.children[state.selectedPartIndex];
  if (!child) {
    elements.selectionDetails.textContent = 'Selected part metadata missing.';
    return;
  }

  elements.selectionDetails.innerHTML = `
    <div><strong>${child.label}</strong></div>
    <div class="helper-text">Index ${child.index + 1} · ${child.solid_count} solid${child.solid_count === 1 ? '' : 's'}</div>
    <div class="helper-text">Volume ${formatNumber(child.volume_mm3, 2)} mm³</div>
    <div class="helper-text">Size ${child.bbox_mm.size.map((value) => formatNumber(value, 2)).join(' × ')} mm</div>
    <div class="helper-text">Center ${child.bbox_mm.center.map((value) => formatNumber(value, 2)).join(', ')} mm</div>
  `;
}

function renderTargetSummary(detail) {
  const modelSummary = detail.model_summary || {};
  const target = detail.target || {};
  elements.targetStatusBadge.textContent = target.status || '-';
  elements.targetSummary.innerHTML = `
    <dt>Name</dt><dd>${target.name || '-'}</dd>
    <dt>Kind</dt><dd>${target.kind || '-'}</dd>
    <dt>Project</dt><dd>${target.project || '-'}</dd>
    <dt>Printable</dt><dd>${target.printable ? 'yes' : 'no'}</dd>
    <dt>Children</dt><dd>${detail.children.length}</dd>
    <dt>Solids</dt><dd>${modelSummary.solid_count ?? '-'}</dd>
    <dt>Volume</dt><dd>${formatNumber(modelSummary.volume_mm3, 2)} mm³</dd>
    <dt>Bounds</dt><dd>${(modelSummary.bbox_mm?.size || []).map((value) => formatNumber(value, 2)).join(' × ')} mm</dd>
    <dt>Detail source</dt><dd>${detail.detail_source || '-'}</dd>
    <dt>Outputs</dt><dd>${Object.keys(detail.artifact_urls || {}).join(', ') || '-'}</dd>
  `;
}

function selectPart(partIndex, { focus = false } = {}) {
  if (!Number.isInteger(partIndex)) {
    state.selectedPartIndex = null;
    state.focusBox = null;
    updatePartVisuals();
    updateSelectionDetails();
    return;
  }

  state.selectedPartIndex = partIndex;
  state.focusBox = state.partBoxes[partIndex] || metadataBoxToSceneBox3(state.targetDetail.children[partIndex]?.bbox_mm);
  updatePartVisuals();
  updateSelectionDetails();

  if (focus && state.focusBox) {
    fitCameraToBox(state.focusBox);
  }

  const row = state.partRows[partIndex];
  if (row) {
    row.scrollIntoView({ block: 'nearest' });
  }
}

function togglePartVisibility(partIndex, visible) {
  if (visible) {
    state.hiddenParts.delete(partIndex);
  } else {
    state.hiddenParts.add(partIndex);
    if (state.selectedPartIndex === partIndex) {
      state.selectedPartIndex = null;
      state.focusBox = null;
    }
  }
  updatePartVisuals();
  updateSelectionDetails();
}

function showAllParts() {
  state.hiddenParts.clear();
  updatePartVisuals();
}

function isolateSelectedPart() {
  if (!Number.isInteger(state.selectedPartIndex)) {
    return;
  }
  state.hiddenParts = new Set(state.targetDetail.children.map((child) => child.index));
  state.hiddenParts.delete(state.selectedPartIndex);
  updatePartVisuals();
}

function hideSelectedPart() {
  if (!Number.isInteger(state.selectedPartIndex)) {
    return;
  }
  togglePartVisibility(state.selectedPartIndex, false);
}

function renderPartList(detail) {
  const children = detail.children || [];
  state.partRows = [];
  elements.partCountBadge.textContent = String(children.length);

  if (!children.length) {
    elements.partList.className = 'part-list empty-state';
    elements.partList.textContent = 'No direct solid children recorded for this target.';
    return;
  }

  elements.partList.className = 'part-list';
  elements.partList.innerHTML = '';

  children.forEach((child) => {
    const row = document.createElement('div');
    row.className = 'part-row';
    row.dataset.label = child.label.toLowerCase();

    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.checked = true;
    checkbox.title = 'Show or hide part';
    checkbox.addEventListener('change', (event) => {
      togglePartVisibility(child.index, event.target.checked);
    });

    const main = document.createElement('button');
    main.type = 'button';
    main.className = 'part-main';

    const titleRow = document.createElement('span');
    titleRow.className = 'part-title-row';
    if (child.color?.hex) {
      const swatch = document.createElement('span');
      swatch.className = 'part-color-swatch';
      swatch.style.backgroundColor = child.color.hex;
      swatch.style.opacity = child.color.rgba?.[3] ?? 1;
      swatch.title = child.color.hex;
      titleRow.appendChild(swatch);
    }

    const title = document.createElement('span');
    title.className = 'part-title';
    title.textContent = child.label;
    titleRow.appendChild(title);

    const meta = document.createElement('span');
    meta.className = 'part-meta';
    meta.textContent = `${child.bbox_mm.size.map((value) => formatNumber(value, 1)).join(' × ')} mm`;
    main.append(titleRow, meta);
    main.addEventListener('click', () => {
      state.interferenceFocus = new Set();
      selectPart(child.index);
    });
    main.addEventListener('dblclick', () => {
      state.interferenceFocus = new Set();
      selectPart(child.index, { focus: true });
    });

    const fitButton = document.createElement('button');
    fitButton.type = 'button';
    fitButton.textContent = 'Fit';
    fitButton.addEventListener('click', (event) => {
      event.stopPropagation();
      state.interferenceFocus = new Set();
      selectPart(child.index, { focus: true });
    });

    row.append(checkbox, main, fitButton);
    elements.partList.appendChild(row);
    state.partRows[child.index] = row;
  });

  updatePartVisuals();
}

function filterPartRows() {
  const query = elements.partSearchInput.value.trim().toLowerCase();
  state.partRows.forEach((row) => {
    if (!row) {
      return;
    }
    const match = !query || row.dataset.label.includes(query);
    row.classList.toggle('hidden', !match);
  });
}

function renderInspectionGallery(detail) {
  const projectionUrls = detail.inspection?.projection_urls || [];
  const overlayUrls = detail.interference?.overlay_urls || [];
  const galleryItems = [
    ...projectionUrls.map((url) => ({ url, label: humanLabelFromUrl(url), type: 'Projection' })),
    ...overlayUrls.map((url) => ({ url, label: humanLabelFromUrl(url), type: 'Interference' })),
  ];

  if (!galleryItems.length) {
    elements.inspectionGallery.className = 'gallery empty-state';
    elements.inspectionGallery.textContent = 'No inspection projections recorded.';
    return;
  }

  elements.inspectionGallery.className = 'gallery';
  const grid = document.createElement('div');
  grid.className = 'gallery-grid';

  galleryItems.forEach((item) => {
    const link = document.createElement('a');
    link.className = 'gallery-card';
    link.href = item.url;
    link.target = '_blank';
    link.rel = 'noreferrer';

    const image = document.createElement('img');
    image.src = item.url;
    image.alt = item.label;

    const label = document.createElement('span');
    label.textContent = `${item.type}: ${item.label}`;

    link.append(image, label);
    grid.appendChild(link);
  });

  elements.inspectionGallery.innerHTML = '';
  elements.inspectionGallery.appendChild(grid);
}

function renderIntentionalInterferences(detail) {
  const intentional = detail.target?.intentional_interferences || [];
  if (!intentional.length) {
    elements.intentionalInterferenceList.innerHTML = '';
    return;
  }

  elements.intentionalInterferenceList.innerHTML = '';
  intentional.forEach((item) => {
    const card = document.createElement('div');
    card.className = 'notice-row';
    card.innerHTML = `
      <h3>${item.first} ↔ ${item.second}</h3>
      <p>${item.reason}</p>
    `;
    elements.intentionalInterferenceList.appendChild(card);
  });
}

function focusInterference(pair) {
  const indices = new Set([
    ...partIndicesForLabel(pair.first),
    ...partIndicesForLabel(pair.second),
  ]);
  state.interferenceFocus = indices;

  const unionBox = new THREE.Box3();
  if (indices.size > 0) {
    indices.forEach((index) => {
      const box = state.partBoxes[index] || metadataBoxToSceneBox3(state.targetDetail.children[index]?.bbox_mm);
      if (box) {
        unionBox.union(box);
      }
    });
  } else {
    const firstBox = metadataBoxToSceneBox3(pair.first_bbox_mm);
    const secondBox = metadataBoxToSceneBox3(pair.second_bbox_mm);
    if (firstBox) {
      unionBox.union(firstBox);
    }
    if (secondBox) {
      unionBox.union(secondBox);
    }
  }

  state.focusBox = unionBox.isEmpty() ? null : unionBox;
  state.selectedPartIndex = indices.size === 1 ? [...indices][0] : null;
  updatePartVisuals();
  updateSelectionDetails();

  if (!unionBox.isEmpty()) {
    fitCameraToBox(unionBox);
  }
}

function renderInterferenceList(detail) {
  const pairs = detail.interference?.check?.interferences || [];
  elements.interferenceCountBadge.textContent = String(pairs.length);
  renderIntentionalInterferences(detail);

  if (!pairs.length) {
    elements.interferenceList.className = 'interference-list empty-state';
    const skipped = detail.interference?.check?.skipped;
    elements.interferenceList.textContent = skipped
      ? 'Interference checking was skipped for this target.'
      : 'No reported interferences.';
    return;
  }

  elements.interferenceList.className = 'interference-list';
  elements.interferenceList.innerHTML = '';

  pairs.forEach((pair) => {
    const row = document.createElement('div');
    row.className = 'interference-row';
    row.innerHTML = `
      <h3>${pair.first} ↔ ${pair.second}</h3>
      <div class="interference-volume">${formatNumber(pair.volume_mm3, 4)} mm³ overlap</div>
    `;
    row.addEventListener('click', () => focusInterference(pair));
    elements.interferenceList.appendChild(row);
  });
}

function updateSectionUI() {
  const axis = elements.sectionAxisSelect.value;
  const box = state.modelBox;
  const boxMm = state.targetDetail?.model_summary?.bbox_mm;
  const enabled = axis !== 'off' && box && boxMm;
  elements.sectionSlider.disabled = !enabled;

  if (!enabled) {
    state.activeClippingPlanes = [];
    applyClippingPlanes();
    elements.sectionReadout.textContent = 'Section view disabled.';
    return;
  }

  const axisIndex = { x: 0, y: 1, z: 2 }[axis];
  const min = box.min.getComponent(axisIndex);
  const max = box.max.getComponent(axisIndex);
  const minMm = boxMm.min[axisIndex];
  const maxMm = boxMm.max[axisIndex];
  const sliderValue = Number(elements.sectionSlider.value) / 1000;
  const position = min + (max - min) * sliderValue;
  const positionMm = minMm + (maxMm - minMm) * sliderValue;
  const normal = new THREE.Vector3(
    axis === 'x' ? 1 : 0,
    axis === 'y' ? 1 : 0,
    axis === 'z' ? 1 : 0,
  );
  if (elements.sectionFlipCheckbox.checked) {
    normal.negate();
  }

  const point = new THREE.Vector3(0, 0, 0);
  point.setComponent(axisIndex, position);
  state.sectionPlane.setFromNormalAndCoplanarPoint(normal, point);
  state.activeClippingPlanes = [state.sectionPlane];
  applyClippingPlanes();

  elements.sectionSliderLabel.textContent = `${axis.toUpperCase()} section`;
  elements.sectionReadout.textContent = `${axis.toUpperCase()} = ${formatNumber(positionMm, 2)} mm`;
}

function setInteractionMode(mode) {
  state.interactionMode = mode;
  if (mode === 'pan') {
    controls.mouseButtons.LEFT = THREE.MOUSE.PAN;
    controls.mouseButtons.RIGHT = THREE.MOUSE.ROTATE;
  } else {
    controls.mouseButtons.LEFT = THREE.MOUSE.ROTATE;
    controls.mouseButtons.RIGHT = THREE.MOUSE.PAN;
  }
  elements.orbitModeButton.classList.toggle('active', mode === 'orbit');
  elements.panModeButton.classList.toggle('active', mode === 'pan');
}

function configureLoadedSceneGeometry(gltf) {
  clearCurrentScene();
  state.loadedScene = gltf.scene;
  scene.add(gltf.scene);

  state.modelBox = new THREE.Box3().setFromObject(gltf.scene);

  gltf.scene.traverse((object) => {
    if (!object.isMesh) {
      return;
    }
    cloneMeshMaterials(object);
    state.meshes.push(object);
  });

  applyClippingPlanes();
  updateSectionUI();
  fitCameraToBox(state.modelBox);
}

function applyTargetDetail(detail) {
  state.targetDetail = detail;
  state.modelMetadataBboxMm = detail.model_summary?.bbox_mm || null;
  state.childIndexByLabel = buildChildIndexByLabel(detail.children || []);
  state.assemblyRoot = state.loadedScene
    ? pickAssemblyRoot(state.loadedScene, detail.children.length)
    : null;
  state.partGroups = [];
  state.partBoxes = [];

  if (state.assemblyRoot) {
    state.partGroups = state.assemblyRoot.children.slice(0, detail.children.length);
  }

  state.partGroups.forEach((group, index) => {
    if (!group) {
      return;
    }
    state.partBoxes[index] = new THREE.Box3().setFromObject(group);
    group.userData.partIndex = index;
    group.traverse((object) => {
      object.userData.partIndex = index;
    });
  });

  renderTargetSummary(detail);
  renderPartList(detail);
  renderInterferenceList(detail);
  renderInspectionGallery(detail);
  updateSelectionDetails();
  updateSectionUI();
}

async function fetchJson(url) {
  const response = await fetch(url);
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `${response.status} ${response.statusText}`);
  }
  return response.json();
}

async function loadTarget(name) {
  if (!name) {
    return;
  }

  const overview = findTargetOverview(name);
  if (!overview?.glb_url) {
    clearCurrentScene();
    renderOverviewOnly(overview, 'No GLB artifact found. Run uv run python main.py first.');
    setOverlay(`Failed to load: No GLB artifact found for ${name}. Run uv run python main.py first.`);
    return;
  }

  const loadToken = Symbol(name);
  state.activeLoadToken = loadToken;
  renderOverviewOnly(overview);
  setOverlay(`Loading ${name} geometry…`);

  try {
    const detailPromise = fetchJson(`/api/targets/${encodeURIComponent(name)}`);
    const gltf = await loader.loadAsync(overview.glb_url);
    if (state.activeLoadToken !== loadToken) {
      disposeObject3D(gltf.scene);
      return;
    }

    configureLoadedSceneGeometry(gltf);
    const url = new URL(window.location.href);
    url.searchParams.set('target', name);
    window.history.replaceState({}, '', url);
    setOverlay(`Loading ${name} metadata…`);

    try {
      const detail = await detailPromise;
      if (state.activeLoadToken !== loadToken) {
        return;
      }
      applyTargetDetail(detail);
      clearOverlay();
    } catch (error) {
      console.error(error);
      if (state.activeLoadToken !== loadToken) {
        return;
      }
      renderOverviewOnly(overview, 'Geometry loaded, but metadata failed to load.');
      elements.interferenceList.className = 'interference-list empty-state';
      elements.interferenceList.textContent = String(error.message || error);
      elements.inspectionGallery.className = 'gallery empty-state';
      elements.inspectionGallery.textContent = 'Inspection outputs unavailable.';
      clearOverlay();
    }
  } catch (error) {
    console.error(error);
    clearCurrentScene();
    renderOverviewOnly(overview, 'Failed to load target geometry.');
    elements.interferenceList.className = 'interference-list empty-state';
    elements.interferenceList.textContent = String(error.message || error);
    elements.inspectionGallery.className = 'gallery empty-state';
    elements.inspectionGallery.textContent = 'Inspection outputs unavailable.';
    setOverlay(`Failed to load: ${error.message || error}`);
  }
}

async function initialize() {
  setOverlay('Loading viewer…');
  state.indexData = await fetchJson('/api/index');
  const requestedTarget = new URL(window.location.href).searchParams.get('target');
  const targets = state.indexData.targets || [];

  elements.targetSelect.innerHTML = '';
  targets.forEach((target) => {
    const option = document.createElement('option');
    option.value = target.name;
    option.textContent = `${target.name} · ${target.project} · ${target.kind}`;
    option.disabled = !target.has_glb;
    elements.targetSelect.appendChild(option);
  });

  const defaultTarget = requestedTarget || state.indexData.default_target || targets.find((target) => target.has_glb)?.name;
  if (defaultTarget) {
    elements.targetSelect.value = defaultTarget;
    await loadTarget(defaultTarget);
  } else {
    setOverlay('No generated GLB targets found. Run uv run python main.py first.');
  }
}

function onCanvasClick(event) {
  if (!state.loadedScene) {
    return;
  }

  const rect = elements.canvas.getBoundingClientRect();
  pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
  pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
  raycaster.setFromCamera(pointer, camera);

  const intersections = raycaster.intersectObjects(state.partGroups.filter(Boolean), true);
  const hit = intersections.find((entry) => entry.object.visible);
  if (!hit) {
    return;
  }

  let object = hit.object;
  while (object && !Number.isInteger(object.userData.partIndex)) {
    object = object.parent;
  }
  if (Number.isInteger(object?.userData?.partIndex)) {
    state.interferenceFocus = new Set();
    selectPart(object.userData.partIndex);
  }
}

function resizeRenderer() {
  const width = elements.canvas.clientWidth;
  const height = elements.canvas.clientHeight;
  if (!width || !height) {
    return;
  }
  renderer.setSize(width, height, false);
  camera.aspect = width / height;
  camera.updateProjectionMatrix();
}

function animate() {
  requestAnimationFrame(animate);
  resizeRenderer();
  controls.update();
  renderer.render(scene, camera);
}

function attachEventHandlers() {
  elements.targetSelect.addEventListener('change', (event) => loadTarget(event.target.value));
  elements.reloadTargetButton.addEventListener('click', () => loadTarget(elements.targetSelect.value));
  elements.fitAllButton.addEventListener('click', () => fitCameraToBox(state.modelBox));
  elements.fitSelectionButton.addEventListener('click', () => fitCameraToBox(currentFocusBox()));
  elements.showAllPartsButton.addEventListener('click', showAllParts);
  elements.isolateSelectedButton.addEventListener('click', isolateSelectedPart);
  elements.hideSelectedButton.addEventListener('click', hideSelectedPart);
  elements.partSearchInput.addEventListener('input', filterPartRows);
  elements.sectionAxisSelect.addEventListener('change', () => {
    elements.sectionSlider.value = '500';
    updateSectionUI();
  });
  elements.sectionFlipCheckbox.addEventListener('change', updateSectionUI);
  elements.sectionSlider.addEventListener('input', updateSectionUI);
  elements.orbitModeButton.addEventListener('click', () => setInteractionMode('orbit'));
  elements.panModeButton.addEventListener('click', () => setInteractionMode('pan'));
  elements.isoViewButton.addEventListener('click', () => setPresetView(new THREE.Vector3(1, -1, 0.75)));
  elements.frontViewButton.addEventListener('click', () => setPresetView(new THREE.Vector3(0, -1, 0)));
  elements.rightViewButton.addEventListener('click', () => setPresetView(new THREE.Vector3(1, 0, 0)));
  elements.topViewButton.addEventListener('click', () => setPresetView(new THREE.Vector3(0, 0, 1), new THREE.Vector3(0, 1, 0)));
  elements.canvas.addEventListener('click', onCanvasClick);
  window.addEventListener('resize', resizeRenderer);
}

attachEventHandlers();
setInteractionMode('orbit');
initialize().catch((error) => {
  console.error(error);
  setOverlay(`Failed to initialize viewer: ${error.message || error}`);
});
animate();
