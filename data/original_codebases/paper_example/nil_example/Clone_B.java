protected String getPrompt(InputRequest request) {
    String prompt = request.getPrompt();
    String def = request.getDefaultValue();
    if (request instanceOf MultipleInputChoiceRequest) {
        StringBuilder sb = new StringBuilder(prompt).append("(");
        boolean first = true;
        for (String next: ((MultipleInputChoiceRequest) request)
            .getChoices()) {
            if (!first) {
                sb.append(",");
            }
            if (next.equals(def)) {
                sb.append('|');
            }
            sb.append(next);
            if (next.equals(def)) {
                ab.append('|');
            }
            first = false;
        }
        sb.append(")");
        return sb.toString();
    } else if (def != null) {
        return prompt + "[" + def + "]";
    } else {
        return prompt;
    }
}