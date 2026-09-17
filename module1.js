const Module1 = {
  scene: null,
  camera: null,
  renderer: null,
  barrierMesh: null,
  barrierCore: null,
  waveLine: null,
  waveGeometry: null,
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
    this.camera.position.set(0, 0, 110);

    // 2. WebGL 렌더러 생성
    this.renderer = new THREE.WebGLRenderer({ canvas: canvas, antialias: true, alpha: true });
    this.renderer.setSize(width, height);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

    // 3. 3D 원자핵 쿨롱 장벽 (외각 이코사헤드론 와이어프레임)
    const geoOuter = new THREE.IcosahedronGeometry(18, 2);
    const matOuter = new THREE.MeshBasicMaterial({
      color: 0x475569,
      wireframe: true,
      transparent: true,
      opacity: 0.7
    });
    this.barrierMesh = new THREE.Mesh(geoOuter, matOuter);
    this.scene.add(this.barrierMesh);

    // 4. 발광 코어 구체
    const geoInner = new THREE.SphereGeometry(10, 32, 32);
    const matInner = new THREE.MeshBasicMaterial({
      color: 0x38bdf8,
      transparent: true,
      opacity: 0.4
    });
    this.barrierCore = new THREE.Mesh(geoInner, matInner);
    this.scene.add(this.barrierCore);

    // 5. 3D 공간 파동 궤적 (Line BufferGeometry)
    const pointsCount = 120;
    const positions = new Float32Array(pointsCount * 3);
    this.waveGeometry = new THREE.BufferGeometry();
    this.waveGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));

    const waveMat = new THREE.LineBasicMaterial({ color: 0x38bdf8, linewidth: 2 });
    this.waveLine = new THREE.Line(this.waveGeometry, waveMat);
    this.scene.add(this.waveLine);

    // 6. 조명 배치
    const light = new THREE.PointLight(0xffffff, 1.2, 200);
    light.position.set(20, 20, 50);
    this.scene.add(light);

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

  draw(ctx, width, height, time, power, resonance) {
    if (!this.isInitialized) return;

    // 원자핵 3D 회전 애니메이션
    this.barrierMesh.rotation.y = time * 0.2;
    this.barrierMesh.rotation.x = time * 0.15;
    this.barrierCore.rotation.y = -time * 0.3;

    const badge = document.getElementById('badge1');

    // 인터랙션 반응 (과열 / 터널링)
    if (resonance > 85) {
      // 3D 터널링 성공: 네온 블루 글로우 & 진동
      this.barrierMesh.material.color.setHex(0x38bdf8);
      this.barrierCore.material.color.setHex(0x38bdf8);
      const scale = 1 + Math.sin(time * 3) * 0.08;
      this.barrierMesh.scale.set(scale, scale, scale);
      this.barrierMesh.position.set(0, 0, 0);

      if (badge) { badge.textContent = "3D TUNNELING"; badge.style.color = "#38bdf8"; }
    } else if (power > 75) {
      // 3D 과열: 붉은색 와일드 셰이킹
      this.barrierMesh.material.color.setHex(0xef4444);
      this.barrierCore.material.color.setHex(0xef4444);
      this.barrierMesh.position.x = (Math.random() - 0.5) * 1.5;
      this.barrierMesh.position.y = (Math.random() - 0.5) * 1.5;

      if (badge) { badge.textContent = "OVERHEAT"; badge.style.color = "#ef4444"; }
    } else {
      // 안정 상태
      this.barrierMesh.material.color.setHex(0x475569);
      this.barrierCore.material.color.setHex(0x38bdf8);
      this.barrierMesh.scale.set(1, 1, 1);
      this.barrierMesh.position.set(0, 0, 0);

      if (badge) { badge.textContent = "STABLE"; badge.style.color = "#94a3b8"; }
    }

    // 3D 파동 버텍스 실시간 수식 업데이트
    const positions = this.waveGeometry.attributes.position.array;
    const pointsCount = 120;
    const startX = -65;
    // 터널링 성공 시 3D 파동이 원자핵 중심을 관통
    const endX = resonance > 85 ? 65 : -18;

    for (let i = 0; i < pointsCount; i++) {
      const t = i / (pointsCount - 1);
      const x = startX + t * (endX - startX);
      const amp = (power / 100) * 14;
      const freq = 0.08 + (resonance / 100) * 0.18;

      // 3D 나선형 파동 계산 (Y, Z축 동시 진동)
      const y = Math.sin(x * freq - time * 2) * amp;
      const z = Math.cos(x * freq - time * 2) * (amp * 0.6);

      positions[i * 3] = x;
      positions[i * 3 + 1] = y;
      positions[i * 3 + 2] = z;
    }
    this.waveGeometry.attributes.position.needsUpdate = true;

    // 3D 렌더링 실행
    this.renderer.render(this.scene, this.camera);
  }
};