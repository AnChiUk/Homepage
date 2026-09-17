const Module2 = {
  scene: null,
  camera: null,
  renderer: null,
  waveguideMesh: null,
  entranceRim: null,
  exitRim: null,
  waveLine: null,
  waveGeometry: null,
  isInitialized: false,

  init(canvasId) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    const container = canvas.parentElement;
    const width = container.clientWidth;
    const height = container.clientHeight;

    // 1. 3D 씬 및 대각선 파스펙티브 카메라 설정
    this.scene = new THREE.Scene();
    this.camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    this.camera.position.set(25, 20, 85);
    this.camera.lookAt(0, 0, 0);

    // 2. WebGL 렌더러
    this.renderer = new THREE.WebGLRenderer({ canvas: canvas, antialias: true, alpha: true });
    this.renderer.setSize(width, height);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

    // 3. 3D 원통 테이퍼드 도파관 (초기 메쉬)
    const length = 80;
    const geo = new THREE.CylinderGeometry(12, 22, length, 32, 1, true);
    geo.rotateZ(-Math.PI / 2); // X축 방향으로 도파관 누르기

    const mat = new THREE.MeshBasicMaterial({
      color: 0x475569,
      wireframe: true,
      transparent: true,
      opacity: 0.35,
      side: THREE.DoubleSide
    });
    this.waveguideMesh = new THREE.Mesh(geo, mat);
    this.scene.add(this.waveguideMesh);

    // 4. 도파관 시작점(입구) 및 끝점(출구) 테두리 링
    const entranceRimGeo = new THREE.RingGeometry(21.5, 22.5, 32);
    entranceRimGeo.rotateY(Math.PI / 2);
    this.entranceRim = new THREE.Mesh(entranceRimGeo, new THREE.MeshBasicMaterial({ color: 0x38bdf8, side: THREE.DoubleSide }));
    this.entranceRim.position.x = -length / 2;
    this.scene.add(this.entranceRim);

    const exitRimGeo = new THREE.RingGeometry(11.5, 12.5, 32);
    exitRimGeo.rotateY(Math.PI / 2);
    this.exitRim = new THREE.Mesh(exitRimGeo, new THREE.MeshBasicMaterial({ color: 0xc084fc, side: THREE.DoubleSide }));
    this.exitRim.position.x = length / 2;
    this.scene.add(this.exitRim);

    // 5. 3D 나선 파동 (버텍스 컬러 그라데이션 적용)
    const pointsCount = 300;
    const positions = new Float32Array(pointsCount * 3);
    const colors = new Float32Array(pointsCount * 3);

    this.waveGeometry = new THREE.BufferGeometry();
    this.waveGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    this.waveGeometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));

    const waveMat = new THREE.LineBasicMaterial({
      vertexColors: true,
      linewidth: 2.5
    });
    this.waveLine = new THREE.Line(this.waveGeometry, waveMat);
    this.scene.add(this.waveLine);

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

  draw(ctx, width, height, time, gap) {
    if (!this.isInitialized) return;

    const length = 80;
    const rIn = 22; // 시작점(입구) 둘레 반지름 (고정)
    // 끝점(출구) 둘레 반지름: 슬라이더 값(Gap)에 따라 3 ~ 22 범위로 변형
    const rOut = Math.max(3, (gap / 250) * 22);

    // 1. 도파관 3D 형상 실시간 업데이터 (입구는 넓고 출구는 좁아지는 깔때기 형상)
    const newGeo = new THREE.CylinderGeometry(rOut, rIn, length, 32, 1, true);
    newGeo.rotateZ(-Math.PI / 2);
    this.waveguideMesh.geometry.dispose();
    this.waveguideMesh.geometry = newGeo;

    // 출구 테두리 링 크기 조정
    const newExitRimGeo = new THREE.RingGeometry(rOut - 0.5, rOut + 0.5, 32);
    newExitRimGeo.rotateY(Math.PI / 2);
    this.exitRim.geometry.dispose();
    this.exitRim.geometry = newExitRimGeo;

    // 2. 도파관 내부 3D 나선 파동 수축 알고리즘
    const positions = this.waveGeometry.attributes.position.array;
    const colors = this.waveGeometry.attributes.color.array;
    const pointsCount = 300;

    let accumulatedPhase = 0;

    for (let i = 0; i < pointsCount; i++) {
      const normX = i / (pointsCount - 1); // 0(시작점) ~ 1(끝점)
      const x = -length / 2 + normX * length;

      // X 위치에 따른 현재 도파관의 반지름 (선형 감소)
      const currentRadius = rIn + normX * (rOut - rIn);

      // 관이 좁아질수록 주파수 변환율(압축 비율) 급증
      const compressionFactor = Math.pow(rIn / currentRadius, 1.25);
      const dx = length / pointsCount;
      accumulatedPhase += 0.15 * compressionFactor * dx;

      // 파동의 진폭은 도파관 내경 한계에 맞춰 수축
      const amp = currentRadius * 0.75;

      // 3D 입체 나선 파동 (Y, Z축 동시 진동)
      const y = Math.sin(accumulatedPhase - time * 2.5) * amp;
      const z = Math.cos(accumulatedPhase - time * 2.5) * amp;

      positions[i * 3] = x;
      positions[i * 3 + 1] = y;
      positions[i * 3 + 2] = z;

      // 색상 변환: 저주파 붉은색(입구) -> 고조파 감마선 보라/자외선(출구)
      const color = new THREE.Color();
      const hue = Math.min(0.8, normX * 0.85); 
      color.setHSL(hue, 1.0, 0.6);

      colors[i * 3] = color.r;
      colors[i * 3 + 1] = color.g;
      colors[i * 3 + 2] = color.b;
    }

    this.waveGeometry.attributes.position.needsUpdate = true;
    this.waveGeometry.attributes.color.needsUpdate = true;

    // 다이내믹 관찰을 위한 3D 카메라 미세 회전
    this.scene.rotation.y = Math.sin(time * 0.2) * 0.12;

    const badge = document.getElementById('badge2');
    if (badge) {
      if (rOut < 8) {
        badge.textContent = "3D HHG GAMMA";
        badge.style.color = "#c084fc";
      } else {
        badge.textContent = "3D TAPERED";
        badge.style.color = "#38bdf8";
      }
    }

    this.renderer.render(this.scene, this.camera);
  }
};