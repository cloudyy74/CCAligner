private int run (Commandline cmd) {
 try {
 Execute exe = new Execute (new LogStreamHandler (this, Project.MSG_INFO, Project.MSG_WARN));
 if (env == null) {
 String [] env = exe.getEnvironment ();
 if (env == null) {
    env = new String [0];
 }
 String [] newEnv = new String [env.length + 1];
 System.arraycopy (env, 0, newEnv, 0, env.length);
 newEnv [env.length] = "SSDIR=" + serverPath;
 exe.setEnvironment (newEnv);
 }
exe.setAntRun (getProject ());
 exe.setWorkingDirectory (getProject ().getBaseDir ());
 exe.setCommandline (cmd.getCommandline ());
 exe.setVMLauncher (false);
 return exe.execute ();
 } catch (IOException e) {
 throw new BuildException (e, getLocation ());
 }
}