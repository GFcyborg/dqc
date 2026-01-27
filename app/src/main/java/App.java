import org.antlr.v4.runtime.*;
import org.antlr.v4.runtime.tree.*;
import java.nio.file.Paths;


public class App {
    public static void main(String[] args) throws Exception {
        CharStream input = CharStreams.fromFileName(Paths.get("app/src/main/openqasm/my.qasm").toString());

        qasm3Lexer lexer = new qasm3Lexer(input);
        CommonTokenStream tokens = new CommonTokenStream(lexer);
        qasm3Parser parser = new qasm3Parser(tokens);

        ParseTree tree = parser.program(); // entry rule
        System.out.println("\nParsed successfully:\n" + tree.toStringTree(parser) );
    }
}
