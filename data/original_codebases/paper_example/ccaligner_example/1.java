protected int run (Commandline cmd) {
try {
Execute exe = new Execute (new LogStreamHandler (this, Project.MSG_INFO, Project.MSG_WARN));
exe.setAntRun (getProject ());
exe.setWorkingDirectory (getProject ().getBaseDir ());
exe.setCommandline (cmd.getCommandline ());
exe.setVMLauncher (false);
return exe.execute ();
} catch (java.io.IOException e) {
throw new BuildException (e, getLocation ());
}
}