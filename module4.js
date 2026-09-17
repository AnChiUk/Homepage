const Module4 = {
  draw(ctx, width, height, time, exponent) {
    ctx.clearRect(0, 0, width, height);

    const centerX = width / 2;
    const centerY = height / 2;
    const badge = document.getElementById('badge4');

    if (badge) badge.textContent = `10^${exponent} m`;

    if (exponent < -5) {
      // 1) 펨토미터: 양자 위상 파문
      ctx.strokeStyle = '#38bdf8';
      for (let r = 10; r < 100; r += 18) {
        ctx.beginPath();
        ctx.arc(centerX, centerY, r + Math.sin(time + r * 0.1) * 6, 0, Math.PI * 2);
        ctx.lineWidth = 1.5;
        ctx.stroke();
      }
    } else if (exponent <= 5) {
      // 2) 나노미터: 결정 격자 3D 구조 시각화
      ctx.strokeStyle = '#c084fc';
      const spacing = 38;
      for (let x = -3; x <= 3; x++) {
        for (let y = -3; y <= 3; y++) {
          const px = centerX + x * spacing;
          const py = centerY + y * spacing;
          ctx.beginPath();
          ctx.arc(px, py, 5 + Math.sin(time * 0.8 + x + y) * 2, 0, Math.PI * 2);
          ctx.stroke();
        }
      }
    } else if (exponent <= 18) {
      // 3) 천문: 항성계 및 케플러 공명 궤도
      ctx.save();
      ctx.shadowColor = '#f59e0b';
      ctx.shadowBlur = 18;
      ctx.fillStyle = '#f59e0b';
      ctx.beginPath(); ctx.arc(centerX, centerY, 14, 0, Math.PI * 2); ctx.fill();
      ctx.restore();

      for (let i = 1; i <= 4; i++) {
        const radius = i * 28;
        ctx.beginPath();
        ctx.arc(centerX, centerY, radius, 0, Math.PI * 2);
        ctx.strokeStyle = 'rgba(148, 163, 184, 0.3)';
        ctx.stroke();

        const px = centerX + Math.cos(time * (0.6 / i)) * radius;
        const py = centerY + Math.sin(time * (0.6 / i)) * radius;
        ctx.beginPath(); ctx.arc(px, py, 4, 0, Math.PI * 2);
        ctx.fillStyle = '#38bdf8'; ctx.fill();
      }
    } else {
      // 4) 우주: Cosmic Web 은하망 시각화
      ctx.strokeStyle = 'rgba(244, 63, 94, 0.5)';
      ctx.lineWidth = 1.2;
      for (let i = 0; i < 14; i++) {
        const angle = (i / 14) * Math.PI * 2;
        const px = centerX + Math.cos(angle + time * 0.03) * 90;
        const py = centerY + Math.sin(angle + time * 0.03) * 90;

        ctx.beginPath();
        ctx.moveTo(centerX, centerY);
        ctx.lineTo(px, py);
        ctx.stroke();

        ctx.beginPath();
        ctx.arc(px, py, 3, 0, Math.PI * 2);
        ctx.fillStyle = '#f43f5e';
        ctx.fill();
      }
    }
  }
};