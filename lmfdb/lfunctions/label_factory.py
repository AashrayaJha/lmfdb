from sage.all import CC, round, ZZ
import re

def round_to_half_str(num, fraction=2):
    num = round(num * 1.0 * fraction)
    if num % fraction == 0:
        return str(ZZ(num/fraction))
    else:
        return str(float(num/fraction))

def CCcmp(z1, z2):
    x1, y1 = z1.real(), z1.imag()
    x2, y2 = z2.real(), z2.imag()

    if x1 < x2:
        return -1
    elif x1 > x2:
        return 1
    elif y1 < y2:
        return -1
    elif y2 < y1:
        return 1
    return 0
def spectral_str(x):
    res = ""
    if x < 0:
        x = -x
        res += "m"
    else:
        res += "p"
    res += "%.2f" % x
    return res

def make_label(L):
    # special $-_.+!*'(),
    #L = db.lfunc_lfunctions.lucky({'Lhash':Lhash},['conductor', 'degree', 'central_character','gamma_factors','algebraic'])
    L = dict(L)
    if L['central_character'].endswith('.1'):
        L['central_character'] = '1.1'
    GR, GC = L['gamma_factors']
    GR = [CC(str(elt)) for elt in GR]
    GR.sort(cmp=CCcmp)
    GC = [CC(str(elt)) for elt in GC]
    GC.sort(cmp=CCcmp)

    rs = ''.join(['r' + round_to_half_str(elt.real()) for elt in GR])
    cs = ''.join(['c' + round_to_half_str(elt.real()) for elt in GC])

    b, e = ZZ(L['conductor']).perfect_power()
    if e == 1:
        conductor = b
    else:
        conductor = "{}p{}".format(b, e)
    beginning = "{}.{}.{}".format(L['degree'], conductor, L['central_character'])
    gammas = "-" + rs + cs + "-"
    if L['algebraic']:
        end = "0"
    else:
        end = ""
        for G in [GR, GC]:
            end += ''.join([spectral_str(elt.imag()) for elt in G])
    label = beginning + gammas + end + "-*"
    return label

def break_label(label):
    inv, rscs, spectral, smth = label.split('-')
    deg, cond, char_mod, char_index = inv.split('.')
    if 'p' in cond:
        b, e = map(int, cond.split('p'))
        cond = b**e
    else:
        cond = int(cond)

    L = {'degree':int(deg),
         'conductor': cond,
         'central_character': ".".join([char_mod, char_index])}
    GR = []
    GC = []
    for elt in re.findall('([r|c][0-9\.]+)', rscs):
        if elt[0] == 'r':
            G = GR
        else:
            G = GC
        G.append(CC(elt[1:]))

    if spectral == '0':
        L['algebraic'] = True
    else:
        L['algebraic'] = False
        for i, elt in enumerate(re.findall('([m|p][0-9\.]+)', spectral)):
            if i > len(GR):
                i -= len(GR)
                G = GC
            else:
                G = GR
            if elt[0] == 'p':
                G[i] += CC(0,1) * CC(elt[1:])
            elif elt[0] == 'm':
                G[i] -= CC(0,1) * CC(elt[1:])
    L['gamma_factors'] = [GR, GC]
    return L
