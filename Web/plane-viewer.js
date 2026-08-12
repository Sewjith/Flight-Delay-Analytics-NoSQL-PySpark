import * as THREE from "three";
import { OBJLoader } from "three/addons/loaders/OBJLoader.js";
import { MTLLoader } from "three/addons/loaders/MTLLoader.js";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";

const container = document.getElementById("plane-3d-container");
const loaderUI = document.getElementById("plane-loader");

if (!container || !loaderUI) {
  console.warn("3D viewer container is missing.");
} else {
  const modelBaseUrl = new URL("./assets/A380/", import.meta.url);
  const fallbackImageUrl = new URL("./assets/A380/a380%20top.png", import.meta.url);
  const isFileProtocol = window.location.protocol === "file:";

  let renderer = null;
  let scene = null;
  let camera = null;
  let controls = null;
  let planeModel = null;
  let animationFrameId = null;
  let resizeObserver = null;

  function setLoaderMessage(message) {
    const label = loaderUI.querySelector("p");
    if (label) {
      label.textContent = message;
    }
  }

  function hideLoader() {
    loaderUI.style.opacity = "0";
    window.setTimeout(() => {
      loaderUI.style.display = "none";
    }, 450);
  }

  function showFallback(message) {
    setLoaderMessage(message);
    loaderUI.classList.add("is-static");

    if (!container.querySelector(".plane-fallback-image")) {
      const image = document.createElement("img");
      image.className = "plane-fallback-image";
      image.src = fallbackImageUrl.href;
      image.alt = "Airbus A380 plane preview";
      container.appendChild(image);
    }

    const spinner = loaderUI.querySelector(".plane-loader-spinner");
    if (spinner) {
      spinner.style.display = "none";
    }
  }

  function initScene() {
    scene = new THREE.Scene();

    camera = new THREE.PerspectiveCamera(
      40,
      container.clientWidth / Math.max(container.clientHeight, 1),
      0.1,
      1000,
    );
    camera.position.set(4, 2.5, 8);

    renderer = new THREE.WebGLRenderer({
      antialias: true,
      alpha: true,
      powerPreference: "high-performance",
    });
    renderer.setSize(container.clientWidth, container.clientHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.2;
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    container.appendChild(renderer.domElement);

    controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.autoRotate = true;
    controls.autoRotateSpeed = 0.6;
    controls.enablePan = false;
    controls.enableZoom = false;
    controls.enableRotate = false;

    scene.add(new THREE.AmbientLight(0x4466aa, 0.6));

    const keyLight = new THREE.DirectionalLight(0xffeedd, 1.8);
    keyLight.position.set(8, 10, 6);
    scene.add(keyLight);

    const fillLight = new THREE.DirectionalLight(0x88aaff, 0.7);
    fillLight.position.set(-6, 4, -2);
    scene.add(fillLight);

    const rimLight = new THREE.PointLight(0x6366f1, 2, 30);
    rimLight.position.set(-4, 2, -8);
    scene.add(rimLight);

    const underGlow = new THREE.PointLight(0x22d3ee, 1, 20);
    underGlow.position.set(0, -3, 4);
    scene.add(underGlow);

    const warmPoint = new THREE.PointLight(0xfbbf24, 0.8, 20);
    warmPoint.position.set(6, 6, -4);
    scene.add(warmPoint);

    const ringGeo = new THREE.RingGeometry(4.5, 5.2, 64);
    const ringMat = new THREE.MeshBasicMaterial({
      color: 0x6366f1,
      transparent: true,
      opacity: 0.08,
      side: THREE.DoubleSide,
    });
    const ring = new THREE.Mesh(ringGeo, ringMat);
    ring.rotation.x = -Math.PI / 2;
    ring.position.y = -1.8;
    scene.add(ring);

    const particleCount = 200;
    const particleGeo = new THREE.BufferGeometry();
    const particlePositions = new Float32Array(particleCount * 3);

    for (let i = 0; i < particleCount; i += 1) {
      particlePositions[i * 3] = (Math.random() - 0.5) * 20;
      particlePositions[i * 3 + 1] = (Math.random() - 0.5) * 10;
      particlePositions[i * 3 + 2] = (Math.random() - 0.5) * 20;
    }

    particleGeo.setAttribute("position", new THREE.BufferAttribute(particlePositions, 3));

    const particles = new THREE.Points(
      particleGeo,
      new THREE.PointsMaterial({
        color: 0x6366f1,
        size: 0.04,
        transparent: true,
        opacity: 0.4,
        blending: THREE.AdditiveBlending,
        depthWrite: false,
      }),
    );
    scene.add(particles);

    const clock = new THREE.Clock();

    function animate() {
      animationFrameId = window.requestAnimationFrame(animate);
      const elapsed = clock.getElapsedTime();

      if (planeModel) {
        planeModel.position.y = 0.2 + Math.sin(elapsed * 0.8) * 0.15;
      }

      const positions = particleGeo.attributes.position.array;
      for (let i = 0; i < particleCount; i += 1) {
        positions[i * 3 + 1] += Math.sin(elapsed + i) * 0.002;
        positions[i * 3] += Math.cos(elapsed * 0.5 + i * 0.1) * 0.001;
      }
      particleGeo.attributes.position.needsUpdate = true;

      ring.material.opacity = 0.05 + Math.sin(elapsed * 2) * 0.03;
      rimLight.intensity = 1.5 + Math.sin(elapsed * 1.5) * 0.5;

      controls.update();
      renderer.render(scene, camera);
    }

    animate();

    function onResize() {
      if (!renderer || !camera) {
        return;
      }

      const width = container.clientWidth;
      const height = Math.max(container.clientHeight, 1);
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
      renderer.setSize(width, height);
    }

    window.addEventListener("resize", onResize);
    resizeObserver = new ResizeObserver(onResize);
    resizeObserver.observe(container);
  }

  function normalizeAndAddModel(object) {
    const box = new THREE.Box3().setFromObject(object);
    const center = box.getCenter(new THREE.Vector3());
    const size = box.getSize(new THREE.Vector3());
    const maxDim = Math.max(size.x, size.y, size.z) || 1;
    const scale = 8 / maxDim;

    object.scale.setScalar(scale);
    object.position.sub(center.multiplyScalar(scale));
    object.position.y += 0.2;
    object.rotation.x = -0.05;
    object.rotation.z = 0.02;

    planeModel = object;
    scene.add(object);
  }

  function loadObjOnly() {
    return new Promise((resolve, reject) => {
      const objLoader = new OBJLoader();
      objLoader.setPath(modelBaseUrl.href);
      objLoader.load("a380.obj", resolve, undefined, reject);
    });
  }

  function loadObjWithMaterials() {
    return new Promise((resolve, reject) => {
      const mtlLoader = new MTLLoader();
      mtlLoader.setPath(modelBaseUrl.href);
      mtlLoader.setResourcePath(modelBaseUrl.href);
      mtlLoader.load(
        "a380.mtl",
        (materials) => {
          materials.preload();

          Object.values(materials.materials).forEach((material) => {
            material.color = new THREE.Color(0xd8dee8);
            material.specular = new THREE.Color(0xffffff);
            material.shininess = 120;
          });

          if (materials.materials.engines) {
            materials.materials.engines.color = new THREE.Color(0x888899);
            materials.materials.engines.shininess = 200;
          }
          if (materials.materials.wings) {
            materials.materials.wings.color = new THREE.Color(0xc0c8d4);
            materials.materials.wings.shininess = 150;
          }

          const objLoader = new OBJLoader();
          objLoader.setMaterials(materials);
          objLoader.setPath(modelBaseUrl.href);
          objLoader.load(
            "a380.obj",
            resolve,
            (xhr) => {
              if (xhr.lengthComputable) {
                const pct = Math.round((xhr.loaded / xhr.total) * 100);
                setLoaderMessage(`Loading 3D model... ${pct}%`);
              }
            },
            reject,
          );
        },
        undefined,
        reject,
      );
    });
  }

  async function loadPlaneModel() {
    const timeoutId = window.setTimeout(() => {
      showFallback("3D preview timed out. Use localhost for the interactive model.");
    }, 12000);

    try {
      const object = await loadObjWithMaterials();
      window.clearTimeout(timeoutId);
      normalizeAndAddModel(object);
      hideLoader();
      return;
    } catch (materialError) {
      console.warn("Material-backed load failed, retrying without MTL.", materialError);
    }

    try {
      const object = await loadObjOnly();
      window.clearTimeout(timeoutId);

      const defaultMaterial = new THREE.MeshPhongMaterial({
        color: 0xd0d8e4,
        specular: 0xffffff,
        shininess: 100,
      });

      object.traverse((child) => {
        if (child.isMesh) {
          child.material = defaultMaterial;
        }
      });

      normalizeAndAddModel(object);
      hideLoader();
    } catch (objError) {
      window.clearTimeout(timeoutId);
      console.error("3D model failed to load.", objError);
      showFallback("3D preview unavailable here. Serve the Web folder over localhost to enable it.");
    }
  }

  if (isFileProtocol) {
    showFallback("3D preview needs a local web server. Open this site through http://localhost.");
  } else {
    try {
      initScene();
      loadPlaneModel();
    } catch (error) {
      console.error("3D viewer setup failed.", error);
      if (renderer && renderer.domElement) {
        renderer.domElement.remove();
      }
      if (animationFrameId) {
        window.cancelAnimationFrame(animationFrameId);
      }
      if (resizeObserver) {
        resizeObserver.disconnect();
      }
      showFallback("3D preview is unavailable in this browser.");
    }
  }
}
