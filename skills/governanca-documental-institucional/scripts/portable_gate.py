#!/usr/bin/env python3
"""Gate portátil: recupera os 3 scripts originais verificados e executa run_gate.py.

Um único arquivo de texto pode ser recuperado como recurso de Skill, copiado
integralmente para ambiente Python e executado, sem internet ou bibliotecas extras.
O hash verifica integridade dos bytes, NÃO autoria nem assinatura criptográfica.
"""
import argparse
import base64
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile

CORE_SHA256 = {'audit_docx.py': '43e708e7f106ec0e238b15856f8227ca53b36f182f38faad8bc9fc7d4d28d737', 'verify_gate_evidence.py': '62ea098be9216b2e64eb4ed256fc102fdae7e4761649c09967942ae807960142', 'run_gate.py': 'b9c225022b17e54b8757d1ac57a8b7ff196555a803973a101fa24aab1957a85a'}
ZIP_SHA256 = 'e361153ecccc075af7a2c8eaae0154dd08235f663cb8842253525b761e8d8ac9'
PAYLOAD_B85 = (
    'P)h>@6aWAK2mk;8AzWl=f^{z&00070000dD003ciWNCC?WN%}5E^v9ZJlk^PMt1M|3hej+Kn(>+V~^L%F<d3f@_OR&NGmBGCme>=B$^~F+}sUPx2P%~k*d7L'
    '$-|aY<)^KE$*cY(Uy^f9cLR+JDUFkzhY<<%<@CAVnjigcZzaXvG|u*Twswk}a+zlz?>u|<>~IyuWiDdoM7-o8jkAYeWf{+y!=2N^v!mCCZ{Usd)ydHhdnYG9'
    'eD@~U*?If$pSdGfQy5pSVrRih?ns_K{6_{8^MMm*vfvMY#!>57u2?c~)+~u5rk=%F$rpkp&JX8b4R-LGC<HI{TiC4RX_3I9(#d!V-z0s^9hOdG4#S;Up2<}j'
    'N4apkce#l6@IU7rpZb9UF3qEOj)#Cr;-^)-rgdSiU=a)O+&ghv<f4Svi-HNs&G%WJBz#uJu!DKDWOA9rQ}gvlnP)q5k*7|<N_^qy7pL&m3=-9X@}^qoHZJCI'
    'QoXrOlYp0k^WZq)DFAl?pB*Nh<BOf0cTVWIcgwOYhI@N*w&W?3L0<3-X3cYvvJ$?E#oiU1yb$?}OBrX2G}(KxzyIl8%Hr(a-8p>XB9UNM-Pt=IIY$?hi)nHy'
    'zGRX+-tp0Qhr1vD{?onJ=O@mKKfK)E_lM4!3um5ZNFpFsl+Wbe+mnmK^U1~W(c9NYhvz{W1v?jCzBxUcoFD(`?~mUe9RpaNTTYYn@+RT#z`@VOsnDNJV9A6P'
    '_-z_T@%O|+?qJ7(f7PtB{OU`VMd$IYS%4lN<w@)DJN*0O%$k41ljOW$GdQsx^E!+4r!N7WTuA&Tm*(Lcc9XBl)(YP-1MizWztkU3#nF;w3-0>*#Ak<ZzlGD@'
    'Wh~`G;QWYR1Ga?vG;r`Sd<M>3rCb2Zdrd_7_dtYGR`A5x{X(G`<g#Qb%a%FfyMRZz9Dw*K>G{1AF_;jEJd1C&M135*40g^=-W*TPFaF`p@j1fdzD4pU?hpuZ'
    '2+|Mubq@A@IK?-dMSz(DdUXV1I~6g$d>Op-6$Y$-X7r2p=oi*fAGcrb!&3J<J3A4dJ4rrciC40PKcvM$5v)W8M_dF#7D-%s?mf=&N4p1OJ*VW?<s_ebSswA`'
    'G}jG&%;U`CNq~bKz_jZU!U2PTXPgnlpm4l*&)w4X{Xmu?E<9haECAvOiqr&@LMgplvwWVH67hCVUvWW0y4wIhC9y0$JsAJRa~crvERt7ox%AusWX|;+U{3W$'
    'mbim@hdb`M*7R!65sn?h&c_!4>Kp_&TX?qtLh9j5-`~+2s%1a|SEx*AKR9rSK+;<E@`A-6&)>6T#gB!^h1Z?xu$4qz>-si+X&sHL1urKOWp0wP!oxQM7>1fn'
    'A7pwni6a2rQmFw<WUHi%;#uh-&MM$>z7tF5ZJu!pP+HG(IYLQ7i5tpE8k4%iCj_~A+<?3LN*~2Kjzvys&=kx;Hd&G&htOP`E|Lx;12}v2{&i$63@3pxO+peL'
    'M(}tXumY5C<VnBYH;x8igis?m63)sakH#aHrqc79JeBawgTcP@g>%s2mNurM6-dtvREj229Jw9wB_Q0_5g?4rB^p$;lVI4B+_?kTekbnX37`awt#fC#zXz><'
    '%jISq8~h?J@N}d7ap$y+V;Xg!U<GZP#2NS0x&t*$a-N0A9vUV19f^T|aA_b(#Z5>jM5uWOU$rEtC5LTJz;)HCxFn4siqW&85JYw43?w_6s%k5I8B1Ee$-AI&'
    'LVR0I)2Di~PMQpZs;ORpGz91`&0^p<f!65VzycqfD6cg~Z82>CJ_R!#on$re)6UM*#v&a&_0y+0Ns-F=XCnW7gCPjbiqdGzCMCEeoOFk@G%dhPk7!lJVKh+v'
    'e_-+17R6x;xZo0$PE&t_g&8=P{05m~<hd#PF&AG0Ovu#q1rGwx<IH-FUtE7&?}G*f*3H1!&@q&8Ied-=Z9p*9qz0EZMvf&TL?k(U?$Se~@La8B(}O3Vr7O-f'
    'Du7nm!Vq}W5gZJy1`SqdEN=?Xy|cDLr{S6;d_G4#z2+0}D2t}_;gh!D8G*Z6f>%pIh8$!I8;&&3dV~+(2P^`G7)Ldp`b3aGZi%6&#L%!pQxs`uQ41g);Zad)'
    'PpHPA@NAK$+C1R%miW%q?9IgO$_IGsv&#ukEr(dCSl(3RAkk=<S`rM{x+7FgJLBPdpk?VJH7u9VsNrGDkZsbMw#B((BGa~5<cTpiY>H+W9?sq4+ML`Q^ZW|q'
    '2C_M#3iq~~Z2SjtAMo?4mIr|cLVnrCx-QADwCQyF*c5r&GU~TR$B;d_?WpHIe(K<d$Ri;(nXEF9ygXU+h)_hh8CH&chHkqW0CsmfUXYKP8?#vn0TXgVlC#ol'
    '0qZ+^&Wpx)I37^TQ`2^lIlgd${g!{x>thhTt3%l*xl^kR7x%zzufU@yAiO~rqA1m~?T12PR;2wP)b?Xlg-s2dvfsdKOwQtXLT-Pkp)-i3SHK6r8qF8W!%W83'
    '!X%ne|NIMlw{a2uwz<*-?N?~*6=F?qfSONzY{VJbt|{H4t=SW1DXZ6Gjua3YCG>@0u3+=4#R<}0duFXs?N48W8K}&8o<yGS{7$Jh>(L|LZ_SysU_;1w$}}Tz'
    '=dRulTwR+{aWXur7-fS8Vg#sW4m?Hu^+Qhak@Ke&%!a`J8bTw?rmUDW$ra$oIfTOuzYG*N$JrWmDQM82P~IgM4?pA7X^c58dtu2@+m^&DMrNLj`>+GG<{yRZ'
    'K028F8ic@gyJ8u|nEC^KQDN*6I&9JxXsKFMz(@6&{=Zd-;}Iv(L!P0!K!E*zK$T6W#OSP?%wwKJvJo?b6P@RmDHE4K-GVJBs@DARk#odgzZpx59QXjNCBM#{'
    'hhLmk>P(Y-mOE3v06#AXBrlj?WiH?|1e&j44)_t$kq9JaL?|Qs@avi<dS%RsV)j<gb1+L91+XFP1@mIuOwU))Ll_UolzK|UFk!$IyQyP^qj3c_En*;+P5~Zn'
    '>M%gmno9|cyMFjt#Q1^%?}DE*htD3r4u;Of$q`O;P7nWhe0Kb`UXcN<mbkqiIEPLVCrbv{0`!4c<O7&6g~KphuH=+wjs?@gGD8&B`zVM(&CM<iz;&9a_T-x$'
    '5vG;c0wn^}@;r%-mQ1)!z5<60eTym<)1xlH`)(N+ls_B{GD+lfy9SrQGf9Ix7YI<oelD^Y5mtW&Qn<sf83^Tla|@nWn`j#Io_)0V(00SVBtcif60Jd6rYvFE'
    'jHJaqS1h5D2#Q-J&>Kq%z&4d&G%{3vXS=RL(?AF20Y`LX3~(-lWuZGq2DJU{PWyG7{*BJ5<fuv(5fc>PqWZSi*JejzjtdZRS4CVn%j6PJ@|#;(s8n1vcAkf3'
    '=$2hNt9NMflr0tWcD6)6yGfL%5CW7m=A~$+f3N7_NuNjpdKspYj-qsVmo8g~)u#`XM4yvdw9_L^l2xKw>jCw^R~hMAeydzIPkbZE#MD}nvkBS)!RO(={$A!Y'
    '{h1;}9_eogEm{~2ilw)3=Wt#Tx=MN5&Nc_r!NhFo3HSXJbnpAAJ5V#xKn1T`o(h5SJUpl#reSjlt+wCG=ica_-plvz$It!Nif!Ya4!8T?6)Nm~jnNF#U?K8V'
    ';T@QizWc1{ADEFQq^->DBc7z*)TEpzW*%{#KBmL44nyVzTp2S0bEk2pd^tNKy+to{4oz%=#M2_vN4)A}a4O?DG!MnE(d__Mf!UrJGBWeVEf^GA*;v*a5e(?X'
    'n)RL#A{zA3Tts5Z%Gt6%6|K_I2B$V2hZ+%g^amb*)dxc!XN>$}a5f_r-WjlLcX0!<NwXm*(1MS;hRsv(v?y;H^l#7{6_3iRp##fA%5FLOOxs{WXbgW>zH675'
    'kAeo%CMvVSd-DCDDyv=YjcbLvvi4tP<ufX;34AxQ>Ey;4q)PxKi(s2uaH=Gxl|;rL{>+@+U4w{S+(!D_&a7zAIJM?I=kxmc2OJ*VzL+J+&2|*%P44$LAft6='
    'AOHi72koCx7lFaS2a}VO=GNoDd!it=Vjv@T!FSJBDf!Ic^@2VEKc4(=05ZdL3#Qi|{wteNJBM~n(37rcDe^VGk|;H~NI`5O%*9c6h5*kT7OCpS5b%JXzEIyD'
    'J?&G@wkjelNZ}EwtE2CLM-|Wo2$9MaHsKN+qTL2?*c`&Ck42r-<Q9=R3!Z=wsxFsphcFcb!&6{~D-tU3=?VNb)_bBE37#94YUFNbIlwW&09f{wN1r`=_PvHv'
    '9U_TSi0>gvdH8pyWK*6H5mS!OkQpfiEYQm6@;-+7wA5P_-k}MKNgE0$rlKB_*IBNBJ0J{VD;z>8SNKRhKlut^0$u=kxlozps`rK^$nva=*SQRwQ#5V)suTc7'
    '3SnH5Qw|!UNmwpdJwS>Ht$+~wY?PIbZgf#cXV0DI5cR-QjeIyRhM6IatShiMs+^h(Ixf=5pjW{rgo7eZG2rV(-Yl0T;DIbG7tYrp!3m*f?-+!k$oGI2807|f'
    'x#R0uvU>P6g{f*ez(0zR0Olk!FL<=N1w_vw?xN6E#tK#1H_IheNvd?0syV?i(M+rJj)oswrKAM6K^%<gk_Sx^)r=NqM7w2R#uHkh6s?i7ZtO{8y9QiAVH{c4'
    '(G3;GO{H0*{jqPQg96p3;rq>uSa#!GBjoyAcoh2XffH|#j{?aF|M+RGNI)TN3?i=-kKaC|K`o)AS!oB=aH+Aq%A&g9hv!w(ddojnM~=dF-H)TDbrJu6z&u7P'
    'G~Ne0_o7RJjuTkX1@m_wM3Kf4c*;wDGpO7*UHSwy3+}4~bxPro{`&AUd{^4jXiK2QM!(Ja=eb(F;A-ZhT{LY}GwE2{T*``^5MPwKf5fA6jNs6kQ9VsQa6b~y'
    'ZKKGiv(NCn3S9@oan<@`_*R=6WExm~NMus`VhCq8q<rXs!KLEo1_J97-|K3rO1ogs8?uGoCRk(l4K{e7f3VYg;8A1cF%TL1C@70eZ_Q5njXH)}cT%5b<EHdR'
    'Ep<st9H=IZ%dMyKy8^YfXUA1$P-)_lO-O3V1)!~aJOHw0^E}ozOc`>AJ=G?@s?3sQkDR=+Y!Iv^@r>BJXY*~z0OEl%E|m^%OOAWCRd6h+a1VQgLdPSTQdGd-'
    '8kxGadr`MT^*8t&wJ<cSl2*#kb?)d;7`y25EIJ0dfe7Q4zGa^lUTOA%!zc!O@{x#BC)0#wmmhkp`ZO4c!9uxsh57|f6JxbR*G{Mb77qWDs<|M6F-t5z^t@>6'
    'Hi{S}8np&^Ohm|2B*~~!wO#()!ernRYsNw@nt=$USQJuNsS@_^DN{o80o-3X$Cb;AIV$Xk;pH-iul-U!kA=hvoZ#)Fxb2ao3x-`I-I``eoKbP^(8x?vUAAUw'
    '>Fb$QsnOO9Lj_%~afjwXYg|*~x<j%-&4(?!>5{7tE4oLNz2I8xF@!e7n5r9IJp83xC5miX1va!@BjUm0N<3Y~b*DYHUSfF=qb7&}C<0V(LB?xupI^^-LB*X|'
    '2CfNYC~oqw&z(AeuzNjpGa!pw7pbTxZ_tQ&YQ>FRpCOedw8I3N3h-h|E~@9YRWqDHcrgGSFD2|Spkj{Q_gAk{r(4Zrq)}CR#C3qBXf;<a=MJlNU0fL00RGp>'
    '*6Kv&17>Tr2f0+e%oXISKyJQao3Ht7G9XlRl;PvuuPg($7u9?$x|^#4!9T{u*YKA};N#tZ+o9Ev6ot0|2GX~klpu>9No&HC$xO^Biv{#qGUw>*2;*qX5&*K%'
    '2;9LkDwhTytmawlEDF1=(i$&V^$fes!FD&FT^g;T;;Q{GRGrT~%BZf>;hu^$CaM8Y_a=86nIJMGkpTUePelxY>cd|!e*%(qbTK(!MgwyFk&)=o=xSh@P-RiF'
    '+)8!jqAsh;C4?`)?yIcS3HWBopaQL`8{mC{R@9)XE04DlwKlX<vsg2!-#kKe9Emw>lgnOH-#=El>m}};t090&w)1KTBN}LP71DhRy<aIm0d&e=L61b}JD5IK'
    'L?6gNn(Hz(X3s<paXQD~j|R6ZvX5brdT(3Bh!9<MK%~{VZTH%C0<i3hr!+U!4b*zENwU`H$`DD`F_Ciw9dDKD178i*g_bt9PDDiMVeHIYGr;m<h2DpK(dLy_'
    ';w9*OPMJrr_kT4RSt`Y|sbJY6j!e3t3Sz-OohC&qhV5dJuBuR{E~>Hcpp8+|TqAWi;~L9<ejUH-4dxELusem``QsM<&GH49DISHROkJ9wOBlF1(E-2J_hed='
    '!Sf48_1jT4u9v7+9=C~$^Dsuz&Gh)ye*(3Y8-m=)MHz$Tri(z^>J)@S=cBv$p3=lQ5jM`&4?kmWW9ZyH8#vEYAX<a#-*<R|?4aQ_!1|?%H3oE0+j<<Kcmn;b'
    ')r`8+T-`xNz3y*8K{cDW-a2m;8hFxg9JJoAbx_jTol<IHi}Gw4ClM&yknYl0jkn;uhNIZ<_iWit(5Pv?ib;_t!%!=Vv8^W22S%41{{nwNJo0GePcZ7e?O_XW'
    'l~KTzNIv`mk%P`YLLd<*OVR}}V(7TfO%|f?N5fBFjvpyZ>HH7?>3{L`D;|BI;)w6So6~AZ!)p|Bt#=<Ql@;I*^;~_RS28TDcj`KyuWm&=(#bC4C@f^BO}dbe'
    '%*zvdOIyu9Y1>lVG?AL{b%?ho^49GMTrKZj%*Z!i%uu^+yue}w$LMO8*7d6{L=BkxBF4%jag2mO>tI6F9n9Ug)ZB$vc*F`~HkMQ>NmWU#UhKyRPpNWnZ)yf^'
    'a_PE*9eDP6_?fEYsmaZw87I1S+;MI6(P{8#c<|}|*xd30U!GdAEgBDDgZoyN!CX5KJeaSNgv!gFFn13}2fKe5ySl5J+732D*C|@L8eWa%R%_tJ!><^Zk)xD#'
    'uwHd<gMO@!x4%CIv~Mk>0X_|yw${@OY&sfq-|}n;VqR*f8lb2O4*+Ag-OFYsY<uc!+R@!6%sEH<Z|m_XNOpB02$<4;MHat)Mvb7&a0Rc2Sc!S%Qy4Cp+QOqR'
    'Rt}p{mbxa{nXn!5<1E?=_cjPI;OpIP+1YM+0}2^9_|o1?#eCti>Hw$jt)60fHq_yv*-d@*8~0Elgo&hmgRp^|%~uIw7FwB(cB$rD9>CoF()5|!={8+EMYxrF'
    'bi83fh?j>HmHl1(jQI5Z%^9)^A{bbwJ8hWsLzDI^AAZ3fGx%+g5j49Nj8B1#hCT_ls!?z&Xo}D+$TTywXsL&`I-3;rw`W`{=A5WCZ1}%1?<kLi-46)7Ssm|q'
    '(3D5IZFEy`U+c5(d~U)!sG6TuA+=78h8xQ2I)9-2zfDP~mM?(5g34#9Vh1*+#pMb|vSfGtaqtNsr}OY-(_ihspr!6-*+~s6I+K8drvKW^5x{E-%=+W9ViDqq'
    '+T&WB-*)SZ#bR?7p=;v^-TF?_WtLxMWZcg6?+JjnKXh=L&b{g_U2OfGtykn{6$_*Cu2eVVKG=t4>($b{>MI#~SA!+prSJ}3y!d1vf12R4Pxk#Mb@E!L#XNh$'
    '%M!i$)_L!)?wyB!bMBV+PI(m<(z=dt1Y}`*Z)lzd0Ea3Nwl+H<0CgPW&>c=pV&akFQJujYhoOd6rvnwGo;uYKcHGR{Bd3EyMeTp(5?f6*`(qxQKA@*{=?+nc'
    'C|C#jhKF>ABiO|xP{%bC>UBG9ZUEjm%?v<KPaVV^s=uw3jEh5gDRlla&$vc@?E%4T^QkqzQY_X2TA}0Cq|{h4sdb<=&M4Z}lGw$hdXTFgEtT(AdTm5~LSx@*'
    'O;e-w%4U@5F>2$k+0RxLTg<fP<1yv9D`kjoboHfO%9ue^=nmcb*M8`?eDJqKV$xr8EE-W>6@P0)|M1T%(>IpsU;44D2M|?K(+`!=5-J#SCyA$AR6p}Wv#6$!'
    ')FlP{aT$}JWkqOye<wH;3zC^r{3bl?Q4?`N^@GU-1ZpzT+42H!3{RLI?z!;p+8yBa<`92@XTzx7UHsi1cfcr_5<-ZP3qAoK*|?%TGmMA~fED5y=4N#5<H_b?'
    'JkTkBQ#I*TQcIo`p?k^&?AAmZr51{E7gM3R_-SSTHWKQj*~713;HsN7h2RhfVlUU`LlO7v607VsO=K@}wn1##*SZx(V1=g@Dzm=&J@r@hm!`0Jh0j)4#<g0`'
    'U_rqbF{n4}ZF7EHNpq?-+l+~3tE$C919iN=J3o2r+&#<klp9y>*$_nHzrk|nr>YC|9^D9R1dDQ#AJvVliwEtx0_+1*bXU_RsFcO(Li0z#)=VXiRRM#*OX3AJ'
    '8RzsXRnGZ0hr2Iceu}MX_={Z*pL4{4YJs3)9>X9|C6e*76bKnu4}00VUtNPJ!1e%~B&7(c)TO3IDuqxOqKE}a&cMOLfkCB!={5ak%>*NU5BrT#V~6gloPVa%'
    'Ej?5EuZ*f!?c{?;?yp4o!K)$E=Pn0WYa?d@`_Wn>)&sBs^m6^VYUx><9(q~V@!MBTJHMUt9WpR*e08G$zN|Tw-XS0-GGT&PGmg~v((InW#xK)g<9MhFuY?iQ'
    'Zv#_&r6<N>H|mvgu%!Y^(>A|vZ$EOelX?#7U?P_c7z$hq{VQmJdQgL=s5-qV30c9CUq>-OQ+hp%D(i#Y*%I~5ICKw!gJ9q7j6~U<=py+zL>DKmG8f9as7r;V'
    'vRYh%YD~3J+xy}CD|IU_?fw#-`&a`TO|$J>^}}||EK04*m`tNzog-!Sj!&D(W<rk=<xa`ZdKZwiNw2R$(c!bRT1bK0B24805I?F*zY_bTtKa0)UD5bofj{bp'
    'oxm+8-G<@{+()h?lSDXLr3D06M2rE?<O-|--K|xn{6S1QEqviWci)5AXh`$!XU5}IX-=;`!r<gw{r#5Ts1L^%0oi-?%@n=AWRb3W5Afb3y`<tdENQ76fkA_N'
    'e0Fw%_^3%e1c<I@1CkecBLi7R;Hh?g{OQGxO%FVGd+iUyg}KyV$37aylW!d?!huald{^DKQhW{`_gLSiK07`=JNf?bs}pM|Fx>zA%fEtMHp1q&SJp{L31>EI'
    'HofL?ouRM?wOnHur7u8OWBNSUaVw%##W*!y`|_=_iUPC|rUa{^z`L~rcuGwg<AEJ1G+K`K`_Xl<vjfj3lror1Anut=(6O9M^nFjHJ4i+8DR<M~`Cm{=0|XQR'
    '000O8001Fe)E3_rj|l((KN|o57XSbNc4cyDW_e#{VRU6*Wp-&~Wo~0-E^v9RS<7x4$rau6D{AaTHxY_XJeeS%!G&Pc7$-B9AZa`a1ffytE|O(6yLzgsIpPfF'
    'Ut)L>I6ziLHrevWa&A>M`$1ARjA&zaJ?^XSJ@?_qUp=XeesU{|C!$!ha$}dO_<Hc@(W48o=DEx`6Kk1m|5c=tv%g%Py=JK@tmaIy7iZ7^#<bx1h#9e>^||Dl'
    'ne9i0&rGB_*L?fW?SF(B4+f{DR%`lvub7dGLe6E%+2z^yv)5NM_ERMoH*77mTlcq^FjiN#(p;J+R+eg^x9@1%3{rI~w8f3N(tHIe#Jxx>%QGw)b*lyB<NBvc'
    't`(C-hC7)Wv)9C&S5_33m@6$8Vl^lrEiWusV<F?2U`uK2_M@gVnF8^gyHCXgD~Loc!JV@Ow-9n!t$3lJB8)bWt5RtT){ByBBkJ!ZH%nZqKi?Wv4CY#`SjjDI'
    'u&{BC&-#$r7=OlYN?9!GBWI<Rs^Iy+Z}KXWHpx_aUmtKQgTdtw=jUe^SF;z%`Ni4GSKrMp*_6dmp$ZX=SR@N$rL8=zll9l*KOS8DCK?W&pS_t~B!8X#-BU=H'
    'BE1tC9bXBuxaEoEx4B5>sw&*N7N%5%;cJm6B|c#9Xf$A*zX<ODd-LW1i;RHPVANzTMV=X2f)iH4><$eFgFz<dcvDk~)W)Rv#F=e`cOw0pFTB1MNvhyfiB`EV'
    '6Lzaq4kcdl+=#9~;-2V<44l+l=3=rl^fjFD2A5vLa>I$cgqMEfgM++d0dLXd8yB<FA6~q=It{V$jLmtz<ZLd|CEO1|;=O07Du~3q3&Xj`<Ty?St(7)lb$#Q$'
    'Wg)HPd163hTKmu#Ur)dJlhb^R=*yDZ4cssu4#!JzpTVPzjfd_&Jq<3Bw~cefGZT9g`D<3(+gKE-%HUnosIv2uKSx7<Q_fkTER%*Df)}ZXiPnfAkZiC4{ZU{F'
    '_J*ElMzY7zMH4FyEbwlrG#t8XR;`%2eJiYrc1(!scp+>Yac$+Cr#A8GMML)0v~7TfskhRYm!&AOIJ*4y^aK}rf$9vMD(yWHA<Y9`aa-}6+=xhpw}y=xLBd*e'
    '%n)H8m}m765aRa3;uvePjE6^sJr^41z|BV~`9FS<XV(lx4wkiCj&;HIL-|t-ocaMwx9<>!tQ5JbnF5|mo+`wyny`rduI9H>xgQMB-^oHD0I1A%0^*JK0_Rh@'
    '`@DeX%H&)CsPU`xTjE|WWGxd+8TV;-y^|N4xaXnn3GasCaY#~Hy}rAtU#15_ls?!U*%%(^jYFUlekQP>0R|u{j%xKPqhvC72}YAHwT-*adN`oG$Emvr5)(8X'
    'XY-r`+?l#_#{}}tA-5q8PG2H<bClNU&h<PTs0xIqbHc=DE~k0-;VxlkyJ$5AK->uxzjRbXzdb^>H1@b=-(i>6)PqtiE|gvYVShnA(TZw{<6vGSbwLE^_^@pR'
    '@`}D70l4aDZEtx^jG$n#n<%)>V9!Y;If<9@Gj+*8(-ljAK973_pDWhz>IyBd8!>Kx*FOs#57~6eBF82Ad@-5_CidG8D|et%PKBq(^VaW|%ayd<_a$FQ{Ceb!'
    '*KD~}P6_h(`}>>W{cGC?HWVPxxnt+v^>r6w*L4UxJFLkLp4O+H15V?m4MpW4@MVYrS**A3D5*CJ9jYOA%u?MkR_jdE_|LvoQoWZ(4~RZ%itZNSUeI^kC)EM`'
    'YOuc2sHu1O))a9MGj8zAm+G)q%1d4+)RhMX?(<0#nth4(l=enK!MIde9cA^?ruw?xx!F&l2Za27`@yQr;X$ioc<&aRw2hq{naAuoB=_COd)2`X7m}`mqE<%2'
    'T?6=u0<8qqTtpP53zaitM-3$nmB67StbOHZiO|lMpGf8weS@$`Q<m%{VpuHvY%b|d*I12w&d*(?II6EryFB_;dH2uJ3EnSvjzLjBJrEjQ)C^7#gz2ZG9S4=U'
    'q(WJD{8q^#Hh?9O#lHd$X*0TMaBoK|B%YfGh422+3$+2Z1+2df_sW94!(E65GO|!fQgN>;U#vJa_Vj-cKI%Wzyr@WFf}q_)XmT7?Je5|SBS`RzUj_?D>yVPW'
    'p5KRwfisvn|AisDl)T)20FzL~9g_RAAhZ2q2Vm31(=p8t>)^B%o36f-!2_;RgQ?iKKBR3(EKMHtyFJ%w$`=WJ7lJTVw;jrZmiHv0-y#2)ouY%(ny(Olyo+7#'
    '4NCYPQ)!hWvO#MuBvl%jus{yV?>%Y&?sfv)wE}$1PAd~~4vDn=h-MO$Tq3eERpdV)tYn{LpoTzp0&PD4lQ@wia7ANGV;G*dNbfq|CTZNKqO@%0{sF$wFbHc8'
    'W`TB4(u{{Xz3soz>^y0QrrneRjYK*eCrJS#CJ7d!c8`&U_~&z!YG2%JQySh8_{`qb;m8UNxbGiW2Aj~k@@`st*37rGE6_u<XaOS@?AIN60@;a+a?hwi_r3ml'
    '(n#An<*UNx%me-T-Ypy_d-{*|cHL1=*k00!`Uwt)`b(|T9`_T^LS#6ciz4(H!yaICx(^g3M!0m{qUPbp=ePjXMDhS?cXag^sAWZu5^nf}+v<`J+;DHxNryg1'
    '?A<*mY)!>KEGS*eCNai)nXygUk-NSb4!$fs-W-tPXRZrbEdKv;9FZjO>&UXR#GbE*mIbnPSVeC-wPFWJeTM+V+WvzI!G-3A?PkoSYv=1Z>$u$XhMCc~R3?fJ'
    's2814^NOivsH~WqIQM4G?Y5*(-_5N}b?b(+()Z|DXfC(^&D6-xL%m*WX?#MY$(!qV!c;e<aV8~b_M_6MNl_28AH{97<K^qA-@=G>#ZirgT*phQCc{vBe5w}}'
    'WutTY(lJV(6g9gm3llO?k_134$2`jt9*)NmnGcm7LGqNQv`3BwJo)s&lammvCoWh|d?_)ad`-echO$zErng4S0~BhwIjIq7gtAx3RG8_0seZUzUW&Y&Mlap4'
    '*U<kwl>Jdxe;lc49vKRyS~R_&LKqS{Ba@6Kq?S&F4-!cAY`PnP)4{Q?@!d~vy$1^WaB3gr{LbFcZO}^4@!6%D^p09n-x0gQJB6Qa*i60B3qeJ(TOICY^HNK)'
    '{_Nu7YyyL0Z^T@8Vm1aHAPm%+!GtvTbkN*%T(W9a(ny=^0UCv=pbs~xlv6+8cOhQb>C<5+U;f^M5?u>8?2zdX@Oy0RsszHFB%vrslE{lr(&5!?>|<j%_#aS9'
    '0|XQR000O8001FeI3XYKEeiku+aLe{3jhEBa&>NBXJK?@E^v9JS>2A?#udKTQ%sx-iiyPCO`4)`p#qD<MiL}m!}%@T1u-H=(sU^fGec^<4t&)oNqbSWK(6`-'
    '`(pjhnIT0=)Y@qm_O8S^bLRYh=gi^z@0~Tyo-K8GrpleD?&^&xKb|~#^ytd|)F@Y5Db})9;_B+hufGz{FJFB6#pPGRnWa^t*^1AuKK)UwbSVpwnXRa;E;dpW'
    'Cc^`#z@f~vERxCO+5JC^kWFo@el4;8wJtY!APT)yR^I=UmUZcBT{oFF;FpL`WiEw!rLx8^uR$nEvolUe2&eI3qPCDiib}d#id+dN?|;QE94t!OQyDx|uQV82'
    'A<J4>ZR}RzLqbYU^tLj#2ETPBty7bgg%&v!uJu-lu-bl~3Htrol&amgk!}MG+OL0grt~Z-S<^zx;W@sxL{%Z{6@+NNyG>K;qWjh?D{C_4T=(Rz`$)%6CZ9if'
    '@kA_`=QK@Mx=?8vCssLA?9?<)pa~S5Tz>c27vF-8$<IV2n_SmvZn9TNbr(&(fAZpsr+@CP?_itNT}s|g)lTPdonp$#Bv&hlDW{}W{CFbpV^!VQvNb@0)sH^;'
    'Jrh6@nWxLUTDfT)CmZ!D*K0)5G!C4aI-3r;v<6N}b31KqoPaJ)v@>KZS@UyOscaE#bx~-iGE?R*YPlkOwKXOAc1lVPPxzU?&`;!JJbK(YBJodB7{DR)rtxe~'
    'Oq^1VABP=mJnh)#$7H0pTo&qx5P_HbM~G6`0e@1bUn}t^ao%IX4l*{C8M$A3PVB|eGudBS9ngEXj&49y<jP_L9A=eSt#qbRxs$pGQZJ1ural~#+l|gP)2K%p'
    '#ll!ITz2hJ|D0Q6^Ym6NQ$#?maxi`>3#WP%rK#z>=quuW#VkawU1iGqUw5kTsq6H*go2qQT&R@CfSq;?parHbfFrs5qxb=*A>9BCKd2=jpdu{^3ix#7K61V^'
    'NyMkW3Bh8Ul7nO>OjB14(n8yrK;n_n7Eu7Ant^D(`#AX|ngQQn@x`~c0S>@YH(P0M(n=z<7tau`GaQwviuO<>015bU2t&Q<os{^1YLkG&R3f0oQ=I;U*Pd8w'
    '>@>POLbhD(@L5>`LTK+TMQH3YizO>4b?^U8u<Kx9@u2{QPxoiXF`wBJW_yF*Qx6(0=*I%4=4Qd3i$f-5Wa>pfmt3|{TS=~5=W{}iIpZ}MVSbUEM?If2uDHxp'
    '?D-Ju8UPRZ8ssRv3ZLo9tnK|T?DkM>f|B?D5)uyDjn#_iAQf=}Y0WUuTMGWA)c2oyYwTS(4t2$H%<_XHf<qsJ@bFP@PY;ub@DQPTlyI^|uB5;`P%=XH`RvFy'
    'Sa^9o*khZFEytiuW<_G99v3*J`^4~5S?g>-s&=wyB;{xyS2)GqPB%yr=w3kkZU-v;hD!Z#OQE+K2#6i5Ot-*`-x9vpa$6w|5NN3EjvQ^(T2mX6qwH6zFd~#k'
    '<GYMD1?X2{*3@Ds(i8N6T(L2(?n%H0aVvs4%i`-}beZ{%2Nt{kJFzmNgfIZgLcb;W_UzFNaj=3E_=BLga;XcQOJs6shM*O7`>z8?(Ql3jWE<DTt$|TZ3HOzN'
    '4PNJ(M{zN&P=t}QAAFFj8es1Fu);a}vJIf?L{@~4)1M=<u!R!}RZb77VxY#wP^;0Oh)<?;@)AU{9uMHt98@7Ihq&J>xTVmTj%Yn+i^OMV7wP%=IsJc!13II;'
    'L7&i?4gIQio9URHP&<4QUc>aPMMu*E(X*(7xrBPYC{Avz2ENrOH&c3&<juBn!Lq>9(lr*v)@53IOr0Sz&|=k#kKzxbzmyTtWG2_;dJ#4CYW{~P?n%czjAu4!'
    '>j`Xg&}Z!R@qq!rQ>#L+H+8y#4Ja2yC`}PJ?y_;z3LhWUTBv{4K_^1Z06jizIDU%|PnETj@K8D`ar>eG+jQ-Kc5jidws-qOu~6g20q;@6$}r1o9;L<AH(Xf-'
    '4#bn+AS=}q?1&#0rHvy5s$R(qZ65c<=~AK5R2)=6z#)0){5&<2k@RfwA>*#;J0SI52&#HrpnF5MO>rT4tti6$o<)$r6K7j0=`V4~NPJ9F;h1sx^vBP7rBp=o'
    'd0Rwh$3>J9dOo*`?kdsjpz%2KT84aKR{Zh0jWI5;dyhb{7Og;vJ|nxCGs&E;CN+14lz>qeq{F66XvgtMP1uktwS?gM5^UQobKVkU9`cE=2UhjBs8Fu40XN6p'
    '0$e>2)h6;tcZo}=)5J2`M_JW`0p22^&mz3wkAC}zxm*pLwn_b}9)b+<4~wUuV<52)(-6@VxY(f<%w_+*?@I5+6kR11{>4d8?lZr0!~s`!gD%DNd?qeB+;|6u'
    '$M{TH*@Q%jE<3p37Qlz^{V#NZFb$P&Y{M1r{y(_$M{h&8Lzx!~adCY9VavsGEYXPEz_RZot>~f`GU8BV+ZJF19zQjT1{CgLQ3p;9KC0;A>OwsF`1F}h$Z*Qc'
    'p55+&{12Ei0DuQ`de{feaTmaK9bz40#;K&=4YNM9<00>@DU=(=wueIx1cynv>#{O{W`3NRyZ<dU{ix(*Zno#WB|o8lpArY)kJVK_@CUWcUlebl2Dcc6k-3{5'
    'u-Mn9Q1QM;>#n%yjWI$ac+*|b(a_NlELB8Jo%}c9&S^wz=$x`QT*tor=IUAWX1qV@JLWAdlDz$Y`lGQx7{|KKP^a*YYs?|kjVW?~cs%~3lsjrVPPGGag-Zd$'
    'LbrFca?^AzB_`!c+bt^;GP~P16HS?IWVwdm-NVJO#`gnl2yy2;n(8Ug^(XI$eU)_7zE`9n@!<P?m)JtVlORGm!*S{H6?&)Dt;ai}{Ec|~fL<3=W%g>l*QpgG'
    'I=Cl4jNIS%VjqZ$Yn^Fk{h9+L$3O0<w+)g|<d7IpF66$YjV5D=?x#^(smnI$WrZW#addKN*BlAY=^H?praYRBw@7J}o2GHtmB>6#WgwsWDF{I9u2Ksc6rUiQ'
    '&wZ@V5$o?nzDIHhE}NnrAC`??%(9KqK;Femn7<?z$6J3l`t+0N`lLXmp?hJOOPl*LLGYikg%CYxx>JOZIw8?U71bj8&KVDu{yzWMyOyr|z&_LlDfkt_nx=}G'
    '=1Id=mJPq*pgTNGA)np<?JB&>@Y4et02Hb=(MidDQR}i{9tKLm3yA!OWd5>oZ411U!Yr*``%Z`6eZU+>jF=|ON;D*+`C4zBc3R4#4!MhwSrFxGwvZpQ_Uc4?'
    'Sh>O@E2{fn*2qV9`lMXTb!nVB;lOa(CBTGki=LPUJ?x^4M=Nf|Z6DlJz%SN&!mF8gI@-0P6sr<n?CATx4Ww^LE6E;@Dyz#u)#}gk{2t#QJy^(&?vCgE`!%!K'
    'm!AFM5LNkca6etC0{8rG1a6o-DDGKus8(sxHXb|_Gx&2a&g<h7PD0WsijP~9zF0@0782%Ul*dP!k4yJ}VB?aEpVx_V3>PCa1gjj74M9RJV&~o2p@+hQv1{=D'
    '=d^xd`|!4Tg3AMD7>qZjVZJfzwSDo?u){}l^yI~htH%+)x0nfj@j<r$-?JWt>PM5&JotHJ3hm7|QoK*i>rRf6TTbKar}-W9TOFrlt?2GF+KtT~qzMC@_~cM?'
    'KM_oQ6A|7)9K_7=<nS~@a-KVoy=_e5H}8ZsCsThP4DX98kCXfN<@9<9J*UG}mFDhUEu$Ar9BF<E?#pBg_%b;RnTvkQb563Hj1218PV|!8uw9^2!u~WZ<yNIB'
    'lcy>5O=%i=UHlDJ*Hhn3#gqR6P)h*<6ay3h000O8001FeWN3nQFB<>=0#g704FCWD0000000000fB^si003ciWNCC?WN%}5E^v8JO928D0~7!N00;m803lq|'
    '7T*<*2><{;8vp<o00000000000001h0a_aX0Cr_^X=Zs}XJK?@UuAY_WMyt+WiD`eP)h*<6ay3h000O8001FeI3XYKEeiku+aLe{3jhEB0000000000fB_yQ'
    '0044zZeM3%bY(7Zc~DCQ1^@s600RI60J#7F0CX?_0000'
)


def sha_bytes(raw):
    return hashlib.sha256(raw).hexdigest()


def unpack_verified():
    try:
        raw = base64.b85decode(''.join(PAYLOAD_B85).encode('ascii'))
    except (ValueError, UnicodeError) as exc:
        raise ValueError('Payload portátil ilegível') from exc
    if sha_bytes(raw) != ZIP_SHA256:
        raise ValueError('SHA-256 do payload portátil divergente; abortar execução')
    try:
        with zipfile.ZipFile(io.BytesIO(raw), 'r') as z:
            found = z.namelist()
            if len(found) != len(CORE_SHA256) or set(found) != set(CORE_SHA256):
                raise ValueError('Inventário do payload divergente')
            parts = {name: z.read(name) for name in CORE_SHA256}
    except (zipfile.BadZipFile, RuntimeError, KeyError) as exc:
        raise ValueError('Arquivo compactado inválido') from exc
    for name, data in parts.items():
        if sha_bytes(data) != CORE_SHA256[name]:
            raise ValueError('SHA-256 de script divergente: ' + name)
    return parts


def verify_sources(parts):
    folder = Path(__file__).resolve().parent
    for name, raw in parts.items():
        original = folder / name
        if not original.is_file() or original.read_bytes() != raw:
            raise ValueError('Fonte original indisponível ou diferente do payload: ' + name)
    return True


def bootstrap_run(docx, output_dir, profile, check_cover, exception_reason=None,
                  bookmark_pages=None):
    if output_dir.exists():
        raise FileExistsError('Pasta de evidências já existe; não sobrescrever: ' + str(output_dir))
    if not docx.is_file():
        raise FileNotFoundError('DOCX não disponível: ' + str(docx))
    # A verificação do payload acontece ANTES de executar qualquer script recuperado.
    parts = unpack_verified()
    before = sha_bytes(docx.read_bytes())
    with tempfile.TemporaryDirectory(prefix='gd-core-verificado-') as temp:
        folder = Path(temp)
        for name, raw in parts.items():
            p = folder / name
            with p.open('xb') as f:
                f.write(raw)
            p.chmod(0o600)
            if sha_bytes(p.read_bytes()) != CORE_SHA256[name]:
                raise ValueError('Erro de gravação do script recuperado: ' + name)
        argv = [sys.executable, str(folder / 'run_gate.py'), str(docx),
                '--output-dir', str(output_dir), '--profile', profile]
        if not check_cover:
            argv += ['--no-standard-cover', '--cover-exception-reason', exception_reason]
        if bookmark_pages:
            argv += ['--bookmark-pages', str(bookmark_pages)]
        proc = subprocess.run(argv, capture_output=True, text=True)
    after = sha_bytes(docx.read_bytes())
    if output_dir.is_dir() and (output_dir / 'execution.json').is_file():
        # Registro adicional de proveniência local; não é log autenticado do host.
        record = {
            'schema': 'gd-portable-bootstrap-1.0',
            'bootstrap': 'portable_gate.py',
            'python': sys.version.split()[0],
            'scripts_sha256': CORE_SHA256,
            'payload_zip_sha256': ZIP_SHA256,
            'artifact_sha256_before': before,
            'artifact_sha256_after': after,
            'artifact_unchanged': before == after,
            'runner_returncode': proc.returncode,
            'scope': 'gate estrutural parcial, não liberação institucional',
            'host_attestation': False,
            'limitations': [
                'A conferência SHA-256 não autentica a origem remota do recurso',
                'O registro é local e não demonstra anterioridade à resposta do host',
                'Gates semântico, visual, workflow e aprovação institucional não são executados aqui'
            ],
        }
        (output_dir / 'bootstrap.json').write_text(
            json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    # Não permitir que o código 0 encubra uma mutação posterior do DOCX.
    if before != after:
        print('ERRO: DOCX alterado durante execução do bootstrap', file=sys.stderr)
        return 1
    if proc.stdout:
        print(proc.stdout, end='')
    if proc.stderr:
        print(proc.stderr, file=sys.stderr, end='')
    return proc.returncode


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('docx', nargs='?', type=Path)
    ap.add_argument('--output-dir', type=Path)
    ap.add_argument('--profile', default='institutional-v3.5',
                    choices=['none', 'institutional-v3.4', 'institutional-v3.5'])
    ap.add_argument('--no-standard-cover', action='store_true')
    ap.add_argument('--cover-exception-reason')
    ap.add_argument('--bookmark-pages', type=Path)
    ap.add_argument('--verify-payload', action='store_true',
                    help='Conferir conteúdo incorporado, sem executar auditoria')
    ap.add_argument('--compare-source', action='store_true',
                    help='Também comparar com os scripts externos da distribuição (teste de empacotamento)')
    args = ap.parse_args(argv)
    if args.compare_source and not args.verify_payload:
        ap.error('--compare-source exige --verify-payload')
    if args.verify_payload:
        parts = unpack_verified()
        if args.compare_source:
            verify_sources(parts)
        print(json.dumps({'payload_verified': True, 'script_sha256': CORE_SHA256,
                          'sources_matched': args.compare_source}, ensure_ascii=False, indent=2))
        return 0
    if not args.docx or not args.output_dir:
        ap.error('DOCX e --output-dir são obrigatórios para executar')
    if args.no_standard_cover and not (args.cover_exception_reason or '').strip():
        ap.error('--no-standard-cover exige --cover-exception-reason')
    if not args.no_standard_cover and args.cover_exception_reason:
        ap.error('--cover-exception-reason exige --no-standard-cover')
    return bootstrap_run(args.docx, args.output_dir, args.profile,
                         not args.no_standard_cover, args.cover_exception_reason,
                         args.bookmark_pages)

if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, zipfile.BadZipFile) as exc:
        print('ERRO:', exc, file=sys.stderr)
        sys.exit(2)
