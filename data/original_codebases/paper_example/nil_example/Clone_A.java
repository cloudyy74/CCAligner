protected String getPrompt(InputRequest request) {
    String prompt = request.getPrompt();
    if (request instanceof MultipleChoiceInputRequest) {
        StringBuffer sb = new StringBuffer(prompt);
        sb.append("(");
        Enumeration e = ((MultipleChoiceInputRequest) request)
            .getChoices().elements();
        boolean first = true;
        while (e.hasMoreElements()) {
            if (!first) {
                sb.append(",");
            }
            sb.append(e.nextElement());
            first = false;
        }
        sb.append(")");
        prompt = sb.toString();
    }
    return prompt;
}