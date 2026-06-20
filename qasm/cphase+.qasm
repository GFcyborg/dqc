gate cphase(θ) a, b
{
  U(0, 0, θ / 2) a;
  cx a, b; //fixed case of CX
  U(0, 0, -θ / 2) b;
  cx a, b; //fixed case of CX
  U(0, 0, θ / 2) b;
}

qubit[2] q;
bit[2] c;
cphase(π / 2) q[0], q[1];

c = measure q;
