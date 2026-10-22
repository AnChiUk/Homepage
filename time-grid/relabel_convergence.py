"""시험 1-b: 각 이름표별로 격자를 촘촘히 하며 연속 극한값(리처드슨 외삽)을 비교"""
from relabel_test_1d import *

maps = [('균일', map_uniform(), 0.1),
        ('사인 늘이기 eps=0.5', map_sine(0.5), 0.1),
        ('sinh 늘이기 lam=10', map_sinh(10.0), 0.04),
        ('대조군: 변환 안 함', map_sine(0.5), 0.1)]
print(f"{'경우':<22}{'h0':>9}{'h0/2':>9}{'h0/4':>9}{'외삽 O2':>10}{'수렴차수':>9}{'외삽 O1':>10}")
out = []
for i, (name, mp, h0) in enumerate(maps):
    naive = (i == 3)
    o1, o2 = [], []
    for h in (h0, h0/2, h0/4):
        r = measure(build(mp, h, naive), 0.25)
        o1.append(r['O1']); o2.append(r['O2'])
    p = np.log2((o2[0]-o2[1])/(o2[1]-o2[2]))
    ext2 = o2[2] + (o2[2]-o2[1])/(2**p - 1)
    ext1 = o1[2] + (o1[2]-o1[1])/3
    out.append((name, ext1, ext2))
    print(f"{name:<22}{o2[0]:>9.3f}{o2[1]:>9.3f}{o2[2]:>9.3f}{ext2:>10.3f}{p:>9.2f}{ext1:>10.5f}")
b = out[0]
print('\n균일 격자 외삽값 대비')
for name, e1, e2 in out[1:]:
    print(f"{name:<22} O1 {100*(e1/b[1]-1):+.3f}%   O2 {100*(e2/b[2]-1):+.3f}%")
