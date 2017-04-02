A set of tools to assist in Taylor Mahler's research paper. The following programs provide content pipelines for the research and can select dialogue of dyads, lines, scenes, and so on. These features will be added as needed, so stay tuned. Further, the format of the shakespeare play to be used is based on Folger text versions of the play available online.

Note that to run the main python script a StanfordCoreNLP server instance must be running on your local machine. The command for starting the server is:

`java -mx5g -cp "*" edu.stanford.nlp.pipeline.StanfordCoreNLPServer -annotators tokenize,ssplit,parse,sentiment -timeout 30000`

This is more efficient than the default annotators as it removes unneeded tools that create extra (and unncessary) overhead.

Enjoy!

-- Matias Grioni
