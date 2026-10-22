"""시험 3-a 보조: 빛 상자의 벽 하중 차이가 격자 분산(h^2)인지 확인"""
import numpy as np
import box_test_3a as B
for h in (0.004, 0.002):
    B.H = h
    g = B.build()
    wt = np.sqrt(B.MU**2 + (10 * B.MU)**2)
    w, U = B.modes(g, wt * 0.99, wt * 1.01)
    fr = [B.inside_fraction(g, U[:, j], w[j]) for j in range(len(w))]
    j = int(np.argmax(fr))
    r = B.run_and_average(g, U[:, j], w[j])
    sp, wl = r['sigp'] / r['E'], -r['wall'] / r['E']
    print(f"h={h}: q*h={10*B.MU*h:.2f}  Σp/ρ={sp:.4f}  3VP/E={wl:.4f}  차이={100*(wl-sp):+.2f}%p  (나′)={1+sp-wl:.4f}")
