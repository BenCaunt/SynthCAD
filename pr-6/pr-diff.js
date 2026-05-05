import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';

const loader = new GLTFLoader();
const MAX_RENDER_PIXEL_RATIO = 1;

let renderFrameRequested = false;

function requestRender() {
  if (!panes || renderFrameRequested) {
    return;
  }
  renderFrameRequested = true;
  window.requestAnimationFrame(() => {
    renderFrameRequested = false;
    if (state.viewerMode !== 'head-only') {
      panes.base.render();
    }
    panes.head.render();
  });
}

const elements = {
  assemblySelect: document.querySelector('#assemblySelect'),
  headOnlyButton: document.querySelector('#headOnlyButton'),
  fitBothButton: document.querySelector('#fitBothButton'),
  isoViewButton: document.querySelector('#isoViewButton'),
  frontViewButton: document.querySelector('#frontViewButton'),
  rightViewButton: document.querySelector('#rightViewButton'),
  topViewButton: document.querySelector('#topViewButton'),
  comparisonSummary: document.querySelector('#comparisonSummary'),
  reviewGallery: document.querySelector('#reviewGallery'),
  baseStatus: document.querySelector('#baseStatus'),
  headStatus: document.querySelector('#headStatus'),
  baseChangedList: document.querySelector('#baseChangedList'),
  headChangedList: document.querySelector('#headChangedList'),
  clearHeadSelectionButton: document.querySelector('#clearHeadSelectionButton'),
  headPartList: document.querySelector('#headPartList'),
};

const state = {
  indexData: null,
  selectedAssembly: null,
  viewerMode: 'diff',
  selectedHeadPartIndex: null,
};

function formatNumber(value, digits = 2) {
  if (typeof value !== 'number' || Number.isNaN(value)) {
    return '-';
  }
  return value.toFixed(digits);
}

function humanLabelFromUrl(url) {
  const base = url.split('/').pop() || url;
  return base.replace(/\.svg$/i, '').replace(/-/g, ' ');
}

function setChipList(element, labels, kind, emptyMessage) {
  element.innerHTML = '';
  if (!labels.length) {
    element.className = 'chip-list empty-state';
    element.textContent = emptyMessage;
    return;
  }

  element.className = 'chip-list';
  for (const label of labels) {
    const chip = document.createElement('span');
    chip.className = `chip ${kind}`;
    chip.textContent = label;
    element.appendChild(chip);
  }
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
  const materials = Array.isArray(mesh.material) ? mesh.material : [mesh.material];
  for (const material of materials.filter(Boolean)) {
    material.userData.baseColor = material.color ? material.color.clone() : null;
    material.userData.baseEmissive = material.emissive ? material.emissive.clone() : null;
    material.userData.baseOpacity = material.opacity;
  }
}

function resetMaterialToBase(material) {
  if (!material) {
    return;
  }
  if (material.color && material.userData.baseColor) {
    material.color.copy(material.userData.baseColor);
  }
  if (material.emissive && material.userData.baseEmissive) {
    material.emissive.copy(material.userData.baseEmissive);
    material.emissiveIntensity = 1.0;
  }
  if ('baseOpacity' in material.userData) {
    material.transparent = material.userData.baseOpacity < 1;
    material.opacity = material.userData.baseOpacity;
  }
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

function triangleCountForGeometry(geometry) {
  if (!geometry) {
    return 0;
  }
  if (geometry.index) {
    return Math.floor((geometry.index.count || 0) / 3);
  }
  const positionCount = geometry.attributes?.position?.count || 0;
  return Math.floor(positionCount / 3);
}

function disposeObjectTree(object) {
  object.traverse((child) => {
    if (child.geometry) {
      child.geometry.dispose();
    }
    if (!child.material) {
      return;
    }
    const materials = Array.isArray(child.material) ? child.material : [child.material];
    for (const material of materials.filter(Boolean)) {
      material.dispose();
    }
  });
}

function materialMergeKey(material) {
  return [
    material.type,
    material.color ? material.color.getHexString() : 'none',
    material.emissive ? material.emissive.getHexString() : 'none',
    material.opacity ?? 1,
    material.transparent ? 'transparent' : 'opaque',
    material.side ?? THREE.FrontSide,
  ].join('|');
}

function mergePartGroupMeshes(partGroup) {
  if (!partGroup || partGroup.isMesh) {
    return {
      meshCountBefore: partGroup?.isMesh ? 1 : 0,
      meshCountAfter: partGroup?.isMesh ? 1 : 0,
      merged: false,
    };
  }

  partGroup.updateWorldMatrix(true, true);
  const rootInverse = partGroup.matrixWorld.clone().invert();
  const groupedGeometries = new Map();
  const groupedMaterials = new Map();
  let meshCountBefore = 0;

  partGroup.traverse((object) => {
    if (!object.isMesh || !object.geometry || !object.material) {
      return;
    }
    if (Array.isArray(object.material)) {
      return;
    }
    meshCountBefore += 1;
    const key = materialMergeKey(object.material);
    const geometry = object.geometry.clone();
    const relativeTransform = rootInverse.clone().multiply(object.matrixWorld);
    geometry.applyMatrix4(relativeTransform);
    if (!groupedGeometries.has(key)) {
      groupedGeometries.set(key, []);
      groupedMaterials.set(key, object.material.clone());
    }
    groupedGeometries.get(key).push(geometry);
  });

  if (meshCountBefore <= 1 || groupedGeometries.size === 0) {
    return {
      meshCountBefore,
      meshCountAfter: meshCountBefore,
      merged: false,
    };
  }

  const mergedMeshes = [];
  for (const [key, geometries] of groupedGeometries.entries()) {
    let mergedGeometry = null;
    if (geometries.length === 1) {
      mergedGeometry = geometries[0];
    } else {
      mergedGeometry = mergeGeometries(geometries, false);
      if (!mergedGeometry) {
        geometries.forEach((geometry) => geometry.dispose());
        return {
          meshCountBefore,
          meshCountAfter: meshCountBefore,
          merged: false,
        };
      }
      geometries.forEach((geometry) => {
        if (geometry !== mergedGeometry) {
          geometry.dispose();
        }
      });
    }
    mergedGeometry.computeBoundingBox();
    mergedGeometry.computeBoundingSphere();
    mergedMeshes.push(new THREE.Mesh(mergedGeometry, groupedMaterials.get(key)));
  }

  const originalChildren = [...partGroup.children];
  for (const child of originalChildren) {
    partGroup.remove(child);
  }
  originalChildren.forEach(disposeObjectTree);
  for (const mergedMesh of mergedMeshes) {
    partGroup.add(mergedMesh);
  }

  return {
    meshCountBefore,
    meshCountAfter: mergedMeshes.length,
    merged: true,
  };
}

function optimizePartGroups(partGroups) {
  const stats = {
    meshCountBefore: 0,
    meshCountAfter: 0,
    triangleCount: 0,
    mergedPartCount: 0,
  };

  for (const partGroup of partGroups) {
    const partStats = mergePartGroupMeshes(partGroup);
    stats.meshCountBefore += partStats.meshCountBefore;
    stats.meshCountAfter += partStats.meshCountAfter;
    if (partStats.merged) {
      stats.mergedPartCount += 1;
    }
    partGroup?.traverse((object) => {
      if (object.isMesh) {
        stats.triangleCount += triangleCountForGeometry(object.geometry);
      }
    });
  }

  return stats;
}

class DiffPane {
  constructor({ canvasId, overlayId, statusElement, accent, selectable = false }) {
    this.canvas = document.querySelector(`#${canvasId}`);
    this.overlay = document.querySelector(`#${overlayId}`);
    this.statusElement = statusElement;
    this.accent = accent;
    this.selectable = selectable;
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0x111827);
    this.camera = new THREE.PerspectiveCamera(45, 1, 0.1, 10000);
    this.camera.position.set(240, -240, 180);
    this.camera.up.set(0, 0, 1);
    this.renderer = new THREE.WebGLRenderer({
      canvas: this.canvas,
      antialias: false,
      powerPreference: 'high-performance',
    });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, MAX_RENDER_PIXEL_RATIO));
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;
    this.controls = new OrbitControls(this.camera, this.canvas);
    this.controls.enableDamping = false;
    this.controls.screenSpacePanning = true;
    this.controls.target.set(0, 0, 0);
    this.controls.update();
    this.loadedScene = null;
    this.modelBox = null;
    this.snapshot = null;
    this.partGroups = [];
    this.changedIndices = new Set();
    this.displayMode = 'diff';
    this.selectedPartIndex = null;
    this.raycaster = new THREE.Raycaster();
    this.pointer = new THREE.Vector2();

    const ambientLight = new THREE.AmbientLight(0xffffff, 0.85);
    this.scene.add(ambientLight);

    const hemiLight = new THREE.HemisphereLight(0xffffff, 0xcbd5e1, 1.35);
    this.scene.add(hemiLight);

    const keyLight = new THREE.DirectionalLight(0xffffff, 1.15);
    keyLight.position.set(200, -280, 240);
    this.scene.add(keyLight);

    const fillLight = new THREE.DirectionalLight(0xffffff, 0.95);
    fillLight.position.set(-220, 180, 160);
    this.scene.add(fillLight);

    const rimLight = new THREE.DirectionalLight(0xffffff, 0.55);
    rimLight.position.set(-120, -140, 260);
    this.scene.add(rimLight);

    this.controls.addEventListener('change', () => requestRender());

    if (this.selectable) {
      this.canvas.addEventListener('click', (event) => this.onCanvasClick(event));
    }
  }

  setOverlay(message) {
    this.overlay.textContent = message;
    this.overlay.classList.remove('hidden');
  }

  clearOverlay() {
    this.overlay.classList.add('hidden');
    this.overlay.textContent = '';
  }

  clearScene() {
    if (this.loadedScene) {
      this.scene.remove(this.loadedScene);
      this.loadedScene.traverse((object) => {
        if (object.geometry) {
          object.geometry.dispose();
        }
        if (!object.material) {
          return;
        }
        const materials = Array.isArray(object.material) ? object.material : [object.material];
        for (const material of materials.filter(Boolean)) {
          material.dispose();
        }
      });
    }
    this.loadedScene = null;
    this.modelBox = null;
    this.snapshot = null;
    this.partGroups = [];
    this.changedIndices = new Set();
    this.selectedPartIndex = null;
    requestRender();
  }

  setDisplayMode(mode) {
    this.displayMode = mode;
    this.applyPartStyling();
    requestRender();
  }

  setPartSelection(index, { focus = false } = {}) {
    this.selectedPartIndex = Number.isInteger(index) ? index : null;
    this.applyPartStyling();
    if (focus && this.selectedPartIndex !== null) {
      this.fitToPart(this.selectedPartIndex);
    } else {
      requestRender();
    }
  }

  clearSelection() {
    this.selectedPartIndex = null;
    this.applyPartStyling();
    requestRender();
  }

  applyPartStyling() {
    for (const [index, group] of this.partGroups.entries()) {
      if (!group) {
        continue;
      }
      group.traverse((object) => {
        if (!object.isMesh) {
          return;
        }
        const materials = Array.isArray(object.material) ? object.material : [object.material];
        for (const material of materials.filter(Boolean)) {
          resetMaterialToBase(material);

          if (this.displayMode === 'diff') {
            if (!this.changedIndices.has(index)) {
              if (material.color) {
                material.color.lerp(new THREE.Color(0x94a3b8), 0.18);
              }
            } else {
              if (material.emissive) {
                material.emissive.setRGB(...this.accent.emissive);
                material.emissiveIntensity = 1.8;
              }
              if (material.color) {
                material.color.setRGB(...this.accent.color);
              }
            }
          }

          if (this.selectedPartIndex !== null) {
            if (index !== this.selectedPartIndex) {
              material.transparent = true;
              material.opacity = Math.max(0.12, (material.userData.baseOpacity || 1) * 0.18);
            } else {
              if (material.emissive) {
                material.emissive.setRGB(...this.accent.emissive);
                material.emissiveIntensity = 1.6;
              }
              if (material.color) {
                material.color.lerp(new THREE.Color(...this.accent.color), 0.25);
              }
            }
          }
        }
      });
    }
  }

  fitToCurrentModel(direction = null, up = null) {
    if (!this.modelBox || this.modelBox.isEmpty()) {
      return;
    }
    const box = this.modelBox;
    const size = box.getSize(new THREE.Vector3());
    const center = box.getCenter(new THREE.Vector3());
    const maxSize = Math.max(size.x, size.y, size.z, 1);
    const radius = maxSize * 1.8;
    const viewDirection = (direction || this.camera.position.clone().sub(this.controls.target) || new THREE.Vector3(1, -1, 0.75)).clone().normalize();
    this.camera.up.copy(up || new THREE.Vector3(0, 0, 1));
    this.camera.position.copy(center.clone().add(viewDirection.multiplyScalar(radius)));
    this.controls.target.copy(center);
    this.camera.near = Math.max(radius / 100, 0.1);
    this.camera.far = Math.max(radius * 20, 1000);
    this.camera.updateProjectionMatrix();
    this.controls.update();
    requestRender();
  }

  fitToPart(partIndex, direction = new THREE.Vector3(1, -1, 0.75), up = new THREE.Vector3(0, 0, 1)) {
    const group = this.partGroups[partIndex];
    if (!group) {
      return;
    }
    const box = new THREE.Box3().setFromObject(group);
    if (box.isEmpty()) {
      return;
    }
    const size = box.getSize(new THREE.Vector3());
    const center = box.getCenter(new THREE.Vector3());
    const maxSize = Math.max(size.x, size.y, size.z, 1);
    const radius = maxSize * 2.2;
    this.camera.up.copy(up);
    this.camera.position.copy(center.clone().add(direction.clone().normalize().multiplyScalar(radius)));
    this.controls.target.copy(center);
    this.camera.near = Math.max(radius / 100, 0.1);
    this.camera.far = Math.max(radius * 20, 1000);
    this.camera.updateProjectionMatrix();
    this.controls.update();
    requestRender();
  }

  onCanvasClick(event) {
    if (!this.selectable || state.viewerMode !== 'head-only' || !this.loadedScene) {
      return;
    }
    const bounds = this.canvas.getBoundingClientRect();
    if (!bounds.width || !bounds.height) {
      return;
    }
    this.pointer.x = ((event.clientX - bounds.left) / bounds.width) * 2 - 1;
    this.pointer.y = -((event.clientY - bounds.top) / bounds.height) * 2 + 1;
    this.raycaster.setFromCamera(this.pointer, this.camera);
    const hits = this.raycaster.intersectObject(this.loadedScene, true);
    const hit = hits.find((candidate) => Number.isInteger(candidate.object?.userData?.partIndex));
    if (!hit) {
      this.clearSelection();
      state.selectedHeadPartIndex = null;
      renderHeadPartList(state.selectedAssembly);
      return;
    }
    const partIndex = hit.object.userData.partIndex;
    this.setPartSelection(partIndex, { focus: false });
    state.selectedHeadPartIndex = partIndex;
    renderHeadPartList(state.selectedAssembly);
  }

  async loadSnapshot(snapshot) {
    this.clearScene();

    if (!snapshot?.glb_url || snapshot?.unavailable) {
      const reason = snapshot?.unavailable_reason || 'Model unavailable in this revision.';
      this.setOverlay(reason);
      this.statusElement.textContent = `${snapshot?.target?.name || 'Unknown target'} · unavailable`;
      return;
    }

    this.setOverlay(`Loading ${snapshot.target.name}…`);
    try {
      this.snapshot = snapshot;
      const gltf = await loader.loadAsync(snapshot.glb_url);
      this.loadedScene = gltf.scene;
      this.scene.add(gltf.scene);

      const root = pickAssemblyRoot(gltf.scene, snapshot.children.length);
      this.partGroups = root ? root.children.slice(0, snapshot.children.length) : [];
      const optimizationStats = optimizePartGroups(this.partGroups);
      this.modelBox = new THREE.Box3().setFromObject(gltf.scene);
      const indexByInstanceKey = new Map(snapshot.children.map((child) => [child.instance_key, child.index]));
      this.changedIndices = new Set(
        (snapshot.changed_instance_keys || [])
          .map((instanceKey) => indexByInstanceKey.get(instanceKey))
          .filter((index) => Number.isInteger(index)),
      );

      for (const [index, group] of this.partGroups.entries()) {
        group?.traverse((object) => {
          if (object.isMesh) {
            cloneMeshMaterials(object);
            object.userData.partIndex = index;
          }
        });
      }

      this.applyPartStyling();
      this.fitToCurrentModel(new THREE.Vector3(1, -1, 0.75));
      this.statusElement.textContent = `${snapshot.target.name} · ${snapshot.children.length} parts · ${snapshot.model_summary.bbox_mm.size.map((value) => formatNumber(value, 1)).join(' × ')} mm · ${Math.round(optimizationStats.triangleCount / 1000)}k tris · ${optimizationStats.meshCountAfter} draws`;
      this.clearOverlay();
      requestRender();
    } catch (error) {
      console.error(error);
      this.setOverlay(`Failed to load: ${error.message || error}`);
      this.statusElement.textContent = 'Failed to load model.';
    }
  }

  resize() {
    const width = this.canvas.clientWidth;
    const height = this.canvas.clientHeight;
    if (!width || !height) {
      return;
    }
    this.renderer.setSize(width, height, false);
    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();
  }

  render() {
    this.resize();
    this.renderer.render(this.scene, this.camera);
  }
}

let panes = {
  base: new DiffPane({
    canvasId: 'baseCanvas',
    overlayId: 'baseOverlay',
    statusElement: elements.baseStatus,
    accent: { color: [0.96, 0.66, 0.12], emissive: [0.72, 0.36, 0.04] },
  }),
  head: new DiffPane({
    canvasId: 'headCanvas',
    overlayId: 'headOverlay',
    statusElement: elements.headStatus,
    accent: { color: [0.16, 0.67, 0.98], emissive: [0.08, 0.35, 0.68] },
    selectable: true,
  }),
};

function renderComparisonSummary(assembly) {
  const comparison = assembly.comparison || {};
  const added = comparison.added || [];
  const modified = comparison.modified || [];
  const removed = comparison.removed || [];
  elements.comparisonSummary.className = 'summary-card';
  elements.comparisonSummary.innerHTML = `
    <div><strong>${assembly.name}</strong></div>
    <dl class="summary-grid">
      <dt>Project</dt><dd>${assembly.project || '-'}</dd>
      <dt>Added</dt><dd>${added.length}</dd>
      <dt>Modified</dt><dd>${modified.length}</dd>
      <dt>Removed</dt><dd>${removed.length}</dd>
      <dt>Unchanged</dt><dd>${comparison.unchanged_count ?? 0}</dd>
    </dl>
  `;
}

function renderReviewGallery(assembly) {
  const outputs = assembly.review_outputs || [];
  if (!outputs.length) {
    elements.reviewGallery.className = 'gallery empty-state';
    elements.reviewGallery.textContent = 'No rendered review outputs.';
    return;
  }

  elements.reviewGallery.className = 'gallery';
  elements.reviewGallery.innerHTML = '';
  for (const output of outputs) {
    const link = document.createElement('a');
    link.className = 'gallery-card';
    link.href = output.url;
    link.target = '_blank';
    link.rel = 'noreferrer';

    const image = document.createElement('img');
    image.src = output.url;
    image.alt = output.view || output.label || 'review output';

    const label = document.createElement('span');
    label.textContent = `${output.kind}: ${output.view || output.label || humanLabelFromUrl(output.url)}`;

    link.append(image, label);
    elements.reviewGallery.append(link);
  }
}

function renderHeadPartList(assembly) {
  const parts = assembly?.head?.children || [];
  if (state.viewerMode !== 'head-only') {
    elements.headPartList.className = 'part-list empty-state';
    elements.headPartList.textContent = 'Enable Head only mode to browse head parts.';
    return;
  }
  if (!parts.length) {
    elements.headPartList.className = 'part-list empty-state';
    elements.headPartList.textContent = 'No selectable head parts recorded.';
    return;
  }

  elements.headPartList.className = 'part-list';
  elements.headPartList.innerHTML = '';
  for (const [index, part] of parts.entries()) {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'part-list-item';
    if (state.selectedHeadPartIndex === index) {
      button.classList.add('active');
    }
    if (part.color?.hex) {
      const swatch = document.createElement('span');
      swatch.className = 'part-color-swatch';
      swatch.style.backgroundColor = part.color.hex;
      swatch.style.opacity = part.color.rgba?.[3] ?? 1;
      swatch.title = part.color.hex;
      button.appendChild(swatch);
    }
    const label = document.createElement('span');
    label.className = 'part-list-label';
    label.textContent = part.label || part.instance_key || `part ${index + 1}`;
    button.appendChild(label);
    button.addEventListener('click', () => {
      state.selectedHeadPartIndex = index;
      panes.head.setPartSelection(index, { focus: false });
      renderHeadPartList(state.selectedAssembly);
    });
    elements.headPartList.append(button);
  }
}

function setViewerMode(mode) {
  state.viewerMode = mode;
  const headOnly = mode === 'head-only';
  document.body.classList.toggle('head-only-mode', headOnly);
  elements.headOnlyButton.classList.toggle('active', headOnly);
  elements.headOnlyButton.textContent = headOnly ? 'Back to diff' : 'Head only';
  panes.base.setDisplayMode('diff');
  panes.head.setDisplayMode(headOnly ? 'default' : 'diff');
  if (!headOnly) {
    state.selectedHeadPartIndex = null;
    panes.head.clearSelection();
  } else if (state.selectedHeadPartIndex !== null) {
    panes.head.setPartSelection(state.selectedHeadPartIndex, { focus: false });
  }
  renderHeadPartList(state.selectedAssembly);
}

async function loadAssembly(name) {
  const assembly = (state.indexData?.assemblies || []).find((item) => item.name === name);
  if (!assembly) {
    return;
  }

  state.selectedAssembly = assembly;
  state.selectedHeadPartIndex = null;
  renderComparisonSummary(assembly);
  renderReviewGallery(assembly);
  setChipList(
    elements.baseChangedList,
    [
      ...(assembly.comparison.modified || []).map((item) => item.label),
      ...(assembly.comparison.removed || []).map((item) => item.label),
    ],
    'base',
    'No base-side changes highlighted.',
  );
  setChipList(
    elements.headChangedList,
    [
      ...(assembly.comparison.modified || []).map((item) => item.label),
      ...(assembly.comparison.added || []).map((item) => item.label),
    ],
    'head',
    'No head-side changes highlighted.',
  );

  await Promise.all([
    panes.base.loadSnapshot(assembly.base),
    panes.head.loadSnapshot(assembly.head),
  ]);
  setViewerMode(state.viewerMode);

  const url = new URL(window.location.href);
  url.searchParams.set('assembly', name);
  window.history.replaceState({}, '', url);
}

async function initialize() {
  const response = await fetch('./data/diff-index.json');
  if (!response.ok) {
    throw new Error(`Failed to load diff-index.json: ${response.status} ${response.statusText}`);
  }
  state.indexData = await response.json();

  const assemblies = state.indexData.assemblies || [];
  elements.assemblySelect.innerHTML = '';
  for (const assembly of assemblies) {
    const option = document.createElement('option');
    option.value = assembly.name;
    option.textContent = `${assembly.name} · ${assembly.project || '-'}`;
    elements.assemblySelect.append(option);
  }

  const requested = new URL(window.location.href).searchParams.get('assembly');
  const selected = requested || state.indexData.default_assembly || assemblies[0]?.name;
  if (selected) {
    elements.assemblySelect.value = selected;
    await loadAssembly(selected);
  }
}

function applyPreset(direction, up = new THREE.Vector3(0, 0, 1)) {
  if (state.viewerMode === 'head-only') {
    if (state.selectedHeadPartIndex !== null) {
      panes.head.fitToPart(state.selectedHeadPartIndex, direction, up);
    } else {
      panes.head.fitToCurrentModel(direction, up);
    }
    return;
  }
  panes.base.fitToCurrentModel(direction, up);
  panes.head.fitToCurrentModel(direction, up);
}


elements.assemblySelect.addEventListener('change', (event) => loadAssembly(event.target.value));
elements.headOnlyButton.addEventListener('click', () => {
  setViewerMode(state.viewerMode === 'head-only' ? 'diff' : 'head-only');
});
elements.clearHeadSelectionButton.addEventListener('click', () => {
  state.selectedHeadPartIndex = null;
  panes.head.clearSelection();
  renderHeadPartList(state.selectedAssembly);
});
elements.fitBothButton.addEventListener('click', () => applyPreset(new THREE.Vector3(1, -1, 0.75)));
elements.isoViewButton.addEventListener('click', () => applyPreset(new THREE.Vector3(1, -1, 0.75)));
elements.frontViewButton.addEventListener('click', () => applyPreset(new THREE.Vector3(0, -1, 0)));
elements.rightViewButton.addEventListener('click', () => applyPreset(new THREE.Vector3(1, 0, 0)));
elements.topViewButton.addEventListener('click', () => applyPreset(new THREE.Vector3(0, 0, 1), new THREE.Vector3(0, 1, 0)));
window.addEventListener('resize', () => {
  panes.base.resize();
  panes.head.resize();
  requestRender();
});

initialize().then(() => {
  requestRender();
}).catch((error) => {
  console.error(error);
  elements.comparisonSummary.className = 'summary-card empty-state';
  elements.comparisonSummary.textContent = `Failed to initialize diff viewer: ${error.message || error}`;
  panes.base.setOverlay('Diff viewer unavailable');
  panes.head.setOverlay('Diff viewer unavailable');
  requestRender();
});
