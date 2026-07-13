qubit q_SOURCE;
qubit q_epr;
qubit q_TO;
bit telept_Zcorrect_q;
bit telept_Xcorrect_q;
reset q_epr;
reset q_TO;
h q_epr;
cx q_epr, q_TO;
cx q_SOURCE, q_epr;
h q_SOURCE;
telept_Zcorrect_q = measure q_SOURCE;
telept_Xcorrect_q = measure q_epr;
if(telept_Zcorrect_q) z q_TO;
if(telept_Xcorrect_q) x q_TO;
// q_SOURCE teleported into q_TO