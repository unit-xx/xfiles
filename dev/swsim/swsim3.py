from datetime import datetime, date
import random
import csv

# simulate path of SWSY(150022) and caculate its NPV.

# 1. sim base (95% 399001, for simplicity)
# 2. distribute return in A/B
# 3. discount to NPV.

mu = 3.0/100
sig = 24.0/100
r = 0.0575
R = 0.0615
A0 = 1.0
B0 = 0.1327

dt = 0.01
N = 100.1 * 1/dt

f = open('npv3b.csv', 'wb')
writer = csv.writer(f)
writer.writerow(('sig', 'B0', 'NPV'))

for sig in [x/100.0 for x in xrange(30,51)]:
    for B0 in [x/10.0 for x in xrange(1,21)]:
        npvsample = []
        for iter in range(400):
            # simulate so many paths and get an averaged NPV.

            # 1a. sim a path
            szczrpath = []
            szczpath = [1.0]
            for i in range(int(N)):
                rday = mu * dt + sig * (dt**0.5) * random.gauss(0, 1)
                rday = rday * 0.95
                szczrpath.append(rday)
                szczpath.append(szczpath[i]*(1+rday))
            del szczpath[0]

            #open('path.dat', 'w').writelines([str(x)+'\n' for x in szczrpath])

            A = A0
            B = B0
            t0 = 0.00
            Amax = 1.0 + t0 * r
            EPS = 1e-6
            #Apath = []
            #Bpath = []
            EDpath = []

            # dynamics of A, B and ED on a path
            for i in range(int(N)):

                # exclude divident for today
                if (t0 % 1 < EPS):
                    if B > 0.1:
                        ED = A - 1.0
                        EDpath.append((A, B, ED))
                        A = 1.0
                        Amax = 1.0
                    else:
                        EDpath.append((A, B, 0.0))
                    t0 = 0.0
                t0 = t0 + dt

                # step to next day
                rd = szczrpath[i]
                Amax = Amax + r * dt
                if (B < 0.1):
                    A = A * (1 + rd)
                    B = B * (1 + rd)
                    if (A < Amax) & (B > 0.1):
                        # B should not be greater than 0.1 when A has not
                        # filled the gap between A and Amax
                        Agap = Amax - A
                        if (B-0.1 < Agap):
                            A = A + B - 0.1
                            B = 0.1
                        else:
                            B = A + B - Amax
                            A = Amax
                    elif (A > Amax):
                        B = A + B - Amax
                        A = Amax
                else:
                    B = B + (A+B)*rd - r * dt
                    A = A + r * dt

                #Apath.append(A)
                #Bpath.append(B)

            #path3tp = zip(szczrpath, szczpath, Apath, Bpath)

            #with open('path.csv', 'wb') as f:
            #    writer = csv.writer(f)
            #    writer.writerows(path3tp)

            EDs = [x[2] for x in EDpath]
            #print sum(EDs)
            #for x in EDpath:
            #    print x

            EDs.reverse()
            NPV = 0.0
            for x in EDs:
                NPV = (NPV + x) / (1 + R)
            #print NPV
            npvsample.append(NPV)
            writer.writerow((sig, B0, NPV))
            f.flush()
        #writer.writerow((mu, r, B0, sum(npvsample)/len(npvsample)))

f.close()
