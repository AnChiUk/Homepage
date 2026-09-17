const Module3 = {
  scene: null,
  camera: null,
  renderer: null,
  protons: [],
  initialPositions: [],
  waveCatalystRings: [],
  goldCore: null,
  electronOrbits: [],
  isInitialized: false,

  init(canvasId) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    const container = canvas.parentElement;
    const width = container.clientWidth;
    const height = container.clientHeight;

    // 1. 3D 씬 및 카메라 설정
    this.scene = new THREE.Scene();
    this.camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    this.camera.position.set(0, 25, 95);
    this.camera.lookAt(0, 0, 0);

    // 2. WebGL 렌더러
    this.renderer = new THREE.WebGLRenderer({ canvas: canvas, antialias: true, alpha: true });
    this.renderer.setSize(width, height);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

    // 3. 79개 수소 이온(Proton, Z=79) 3D 볼 생성 및 초기 배치 지정
    this.protons = [];
    this.initialPositions = [];
    const protonGeo = new THREE.SphereGeometry(1.2, 16, 16);
    const protonMat = new THREE.MeshBasicMaterial({ color: 0x38bdf8 });

    for (let i = 0; i < 79; i++) {
      const mesh = new THREE.Mesh(protonGeo, protonMat.clone());
      // 초기 구형 무작위 분포
      const u = Math.random();
      const v = Math.random();
      const theta = u * 2.0 * Math.PI;
      const phi = Math.acos(2.0 * v - 1.0);
      const r = 25 + Math.random() * 20;

      const x = r * Math.sin(phi) * Math.cos(theta);
      const y = r * Math.sin(phi) * Math.sin(theta);
      const z = r * Math.cos(phi);

      mesh.position.set(x, y, z);
      this.scene.add(mesh);
      this.protons.push(mesh);
      this.initialPositions.push(new THREE.Vector3(x, y, z));
    }

    // 4. 파동 촉매 필드 (3D 보라색 토러스 파동 링 3개)
    this.waveCatalystRings = [];
    for (let i = 0; i < 3; i++) {
      const ringGeo = new THREE.TorusGeometry(30 - i * 6, 0.6, 16, 64);
      const ringMat = new THREE.MeshBasicMaterial({
        color: 0xc084fc,
        wireframe: true,
        transparent: true,
        opacity: 0.4
      });
      const ring = new THREE.Mesh(ringGeo, ringMat);
      ring.rotation.x = Math.PI / 3 * i;
      ring.rotation.y = Math.PI / 4 * i;
      this.scene.add(ring);
      this.waveCatalystRings.push(ring);
    }

    // 5. 금(Au) 완성 원자핵 (중앙 황금 글로우 코어)
    const goldGeo = new THREE.SphereGeometry(12, 32, 32);
    const goldMat = new THREE.MeshBasicMaterial({
      color: 0xf59e0b,
      transparent: true,
      opacity: 0
    });
    this.goldCore = new THREE.Mesh(goldGeo, goldMat);
    this.scene.add(this.goldCore);

    // 6. 전자 궤도 링
    this.electronOrbits = [];
    for (let i = 1; i <= 3; i++) {
      const orbitGeo = new THREE.RingGeometry(16 * i * 0.5, 16.5 * i * 0.5, 64);
      const orbitMat = new THREE.MeshBasicMaterial({
        color: 0xfbbf24,
        side: THREE.DoubleSide,
        transparent: true,
        opacity: 0
      });
      const orbit = new THREE.Mesh(orbitGeo, orbitMat);
      orbit.rotation.x = Math.PI / 2 + (i * 0.2);
      this.scene.add(orbit);
      this.electronOrbits.push(orbit);
    }

    this.isInitialized = true;
  },

  resize(canvasId) {
    if (!this.isInitialized) return;
    const canvas = document.getElementById(canvasId);
    const container = canvas.parentElement;
    const width = container.clientWidth;
    const height = container.clientHeight;

    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(width, height);
  },

  draw(ctx, width, height, time, progress) {
    if (!this.isInitialized) return;

    // progress: 0.0 ~ 1.0 (타임라인 진행도)
    const badge = document.getElementById('badge3');

    // 카메라 및 촉매 파동 회전
    this.scene.rotation.y = time * 0.2;

    // 1단계: 수소 이온화 (0.0 ~ 0.25)
    // 2단계: 파동 촉매 수축 (0.25 ~ 0.60)
    // 3단계: 핵융합 재배열 (0.60 ~ 0.85)
    // 4단계: 금 원자 결정화 (0.85 ~ 1.0)

    if (progress < 0.25) {
      if (badge) { badge.textContent = "H⁺ IONIZED"; badge.style.color = "#38bdf8"; }
    } else if (progress < 0.60) {
      if (badge) { badge.textContent = "CATALYSIS"; badge.style.color = "#c084fc"; }
    } else if (progress < 0.85) {
      if (badge) { badge.textContent = "FUSING"; badge.style.color = "#ef4444"; }
    } else {
      if (badge) { badge.textContent = "Au (Z=79)"; badge.style.color = "#fbbf24"; }
    }

    // 파동 촉매 링 반응 (진행도에 따라 중앙으로 집속)
    this.waveCatalystRings.forEach((ring, idx) => {
      const scale = Math.max(0.1, 1 - progress * 0.8);
      ring.scale.set(scale, scale, scale);
      ring.material.opacity = progress < 0.85 ? 0.3 + Math.sin(time * 3 + idx) * 0.2 : (1 - progress) * 2;
    });

    // 79개 수소 이온 3D 수축 파티클 연산
    this.protons.forEach((p, idx) => {
      const initPos = this.initialPositions[idx];

      if (progress < 0.85) {
        // 진행도에 맞춰 중심점(0,0,0)으로 나선형 수축
        const factor = Math.max(0.08, 1 - (progress / 0.85));
        const spiralAngle = progress * Math.PI * 6 + idx;

        p.position.x = initPos.x * factor * Math.cos(spiralAngle * 0.1);
        p.position.y = initPos.y * factor;
        p.position.z = initPos.z * factor * Math.sin(spiralAngle * 0.1);

        // 색상 전환: 파란색 -> 빨간색(융합열)
        const hue = 0.6 - (progress / 0.85) * 0.6;
        p.material.color.setHSL(Math.max(0, hue), 1.0, 0.6);
        p.visible = true;
      } else {
        // 융합 완료 후 금 원자핵 속으로 흡수
        p.visible = false;
      }
    });

    // 완성된 금(Au) 원자핵 및 전자 궤도 페이드인
    if (progress >= 0.70) {
      const goldAlpha = (progress - 0.70) / 0.30;
      this.goldCore.material.opacity = goldAlpha * 0.9;
      this.goldCore.scale.setScalar(0.5 + goldAlpha * 0.5);

      this.electronOrbits.forEach((orbit, idx) => {
        orbit.material.opacity = goldAlpha * 0.6;
        orbit.rotation.z = time * (idx + 1) * 0.5;
      });
    } else {
      this.goldCore.material.opacity = 0;
      this.electronOrbits.forEach(orbit => orbit.material.opacity = 0);
    }

    this.renderer.render(this.scene, this.camera);
  }
};