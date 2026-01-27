/*
 * Copyright (C) 2026 Giacomo Fagioli (giacomofagioli_at_gmail.com)
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <https://www.gnu.org/licenses/>.
 *
 * The full license text is available in the LICENSE file
 * in the root directory of this project.
 */


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
