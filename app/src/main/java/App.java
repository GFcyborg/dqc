import org.antlr.v4.runtime.*;
import org.antlr.v4.runtime.tree.*;

public class App {
    public static void main(String[] args) throws Exception {
        CharStream input = CharStreams.fromStream( App.class.getResourceAsStream("my.qasm") ); //symlink in ./app/src/main/resources/

        qasm3Lexer lexer = new qasm3Lexer(input);
        CommonTokenStream tokens = new CommonTokenStream(lexer);
        qasm3Parser parser = new qasm3Parser(tokens);

        ParseTree tree = parser.program(); // entry rule
        System.out.println("\nParsed successfully:\n" + tree.toStringTree(parser) );
    }
}
