// Polyglot fixture — null-return-on-some-path.
// lookup() returns null when id is negative (line 8). Caller at line 15 derefs.
// Parses clean; spotbugs NP_NULL_ON_SOME_PATH would flag line 15.

public class Sample {
    static String lookup(int id) {
        if (id < 0) {
            return null;
        }
        return "user-" + id;
    }

    public static void main(String[] args) {
        String name = lookup(-1);
        System.out.println(name.length());
    }
}
