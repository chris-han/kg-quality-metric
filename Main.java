// Input:
// String[] inputStrings = {"A,B,C", "D,E,F", "J,G,C", "F,H,Q", "A,I,C","D,X,Q","D,X,F","A,M,C"};

//Output:
// Graph-1
// Node A --> C 
// Node Q --> F D 
// Node C --> A J 
// Node D --> F Q 
// Node F --> D Q 
// Node J --> C 
// Number of nodes: 6
// Number of components: 2

// Graph-2
// Node A --> C 
// Node C --> A 
// Node D --> F 
// Node F --> D 
// Number of nodes: 4
// Number of components: 2

// Graph-3
// Node A --> C 
// Node C --> A 
// Number of nodes: 2
// Number of components: 1




import java.util.*;
import java.io.FileReader;
import java.io.FileWriter;
import org.json.simple.JSONObject;
import org.json.simple.parser.JSONParser;
import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.FileReader;
import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import org.apache.commons.text.similarity.JaroWinklerSimilarity;

// Class to represent a graph node
class GraphNode {
    List<String> values;
    List<String> adjacentNodes;

    public GraphNode(List<String> values) {
        this.values = values;
        this.adjacentNodes = new ArrayList<>();
    }
}

// Class to represent an undirected graph
class Graph {
    Map<String, GraphNode> nodes;

    public Graph() {
        this.nodes = new HashMap<>();
    }

    // Method to add an edge between two nodes (undirected)
    public void addEdge(List<String> node1, List<String> node2) {
        String key1 = getKey(node1);
        String key2 = getKey(node2);

        if (!nodes.containsKey(key1)) {
            nodes.put(key1, new GraphNode(node1));
        }
        if (!nodes.containsKey(key2)) {
            nodes.put(key2, new GraphNode(node2));
        }
        nodes.get(key1).adjacentNodes.add(key2);
        nodes.get(key2).adjacentNodes.add(key1); // Adding for undirected graph
    }

    // Helper method to get a string key from a list of values
    private String getKey(List<String> values) {
        StringBuilder keyBuilder = new StringBuilder();
        for (String value : values) {
            keyBuilder.append(value.toLowerCase()).append("_");
        }
        return keyBuilder.toString();
    }

    // Method to perform depth-first search
    private void dfs(String key, Set<String> visited, List<String> component) {
        visited.add(key);
        component.addAll(nodes.get(key).values);
        for (String adjKey : nodes.get(key).adjacentNodes) {
            if (!visited.contains(adjKey)) {
                dfs(adjKey, visited, component);
            }
        }
    }

    // Method to calculate components
    public List<List<String>> getComponents() {
        Set<String> visited = new HashSet<>();
        List<List<String>> components = new ArrayList<>();
        for (String key : nodes.keySet()) {
            if (!visited.contains(key)) {
                List<String> component = new ArrayList<>();
                dfs(key, visited, component);
                components.add(component);
            }
        }
        return components;
    }

    // Method to check if an edge exists
    public boolean edgeExists(List<String> node1, List<String> node2) {
        String key1 = getKey(node1);
        String key2 = getKey(node2);
        return nodes.containsKey(key1) && nodes.containsKey(key2) &&
               nodes.get(key1).adjacentNodes.contains(key2);
    }

    // Method to print the graph
    public void printGraph() {
        for (String key : nodes.keySet()) {
            List<String> values = nodes.get(key).values;
            System.out.print("Node [");
            for (int i = 0; i < values.size(); i++) {
                System.out.print(values.get(i));
                if (i < values.size() - 1) {
                    System.out.print(", ");
                }
            }
            System.out.print("] --> ");
            for (String adjKey : nodes.get(key).adjacentNodes) {
                List<String> adjValues = nodes.get(adjKey).values;
                System.out.print("[");
                for (int i = 0; i < adjValues.size(); i++) {
                    System.out.print(adjValues.get(i));
                    if (i < adjValues.size() - 1) {
                        System.out.print(", ");
                    }
                }
                System.out.print("] ");
            }
            System.out.println();
        }
    }

    // Method to get the total number of nodes
    public int numberOfNodes() {
        return nodes.size();
    }

    // Method to get the number of components
    public int numberOfComponents() {
        return getComponents().size();
    }

    // Method to collect all pos elements present in the graph nodes
    public Set<String> collectPosElements() {
        Set<String> posElements = new HashSet<>();
        for (String key : nodes.keySet()) {
            List<String> values = nodes.get(key).values;
            posElements.addAll(values);
        }
        return posElements;
    }

    // Method to count the number of pos elements in the graph nodes
    public int countPosElements() {
        Set<String> posElements = collectPosElements();
        return posElements.size();
    }
}

public class Main {
    static JaroWinklerSimilarity jw = new JaroWinklerSimilarity();

    static double calculate_d(Graph graph, int n_ideal, int n_nonideal, double total_nouns_sum, Map<String, Double> noun_similarity_score) {
        double numberOfNodes = (double) graph.numberOfNodes();
        double numberOfComponents = (double) graph.numberOfComponents();

        double term1 = Math.abs(1.0 - numberOfNodes / (double) n_nonideal);
        
        // Updated formula for Term-2
        double sumDiff = 0.0;
        for (double similarity : noun_similarity_score.values()) {
            sumDiff += (1.0 - similarity);
        }
        double term2 = Math.abs(n_ideal - n_nonideal) + sumDiff;    

        double term3 = Math.abs(1.0 - numberOfComponents);

        // System.out.println("Noun Similarity Scores:");
        // for (Map.Entry<String, Double> entry : noun_similarity_score.entrySet()) {
        //     System.out.println(entry.getKey() + " : " + entry.getValue());
        // }

        return ((double)n_nonideal/total_nouns_sum)*(term1 + term2 + term3);
    }
    
    /**
     * Enhanced verb metric calculation with polarity penalty support.
     * 
     * @param extractedTriples List of extracted triples (3-tuple or 4-tuple)
     * @param idealTriples List of ideal triples (3-tuple or 4-tuple)
     * @param pos_verbs List of POS verbs for the sentence
     * @param lambda Polarity penalty weight (default: 0.1)
     * @return Calculated verb metric dV(G1, Gi) with polarity penalty
     */
    static double calculate_verb_metric_with_polarity(
        List<List<String>> extractedTriples, 
        List<List<String>> idealTriples, 
        List<String> pos_verbs, 
        double lambda
    ) {
        if (extractedTriples.isEmpty()) {
            return 1.0;
        }
        
        // Extract relations from extracted triples
        List<String> relations = new ArrayList<>();
        List<String> extractedPolarities = new ArrayList<>();
        
        for (List<String> tuple : extractedTriples) {
            if (tuple.size() > 1) {
                relations.add(tuple.get(1)); // predicate is at index 1
                // If 4-tuple, extract polarity; otherwise default to "positive"
                if (tuple.size() >= 4) {
                    extractedPolarities.add(tuple.get(3));
                } else {
                    extractedPolarities.add("positive");
                }
            }
        }
        
        // Extract ideal relations and polarities
        List<String> idealRelations = new ArrayList<>();
        List<String> idealPolarities = new ArrayList<>();
        
        for (List<String> tuple : idealTriples) {
            if (tuple.size() > 1) {
                idealRelations.add(tuple.get(1)); // predicate is at index 1
                // If 4-tuple, extract polarity; otherwise default to "positive"
                if (tuple.size() >= 4) {
                    idealPolarities.add(tuple.get(3));
                } else {
                    idealPolarities.add("positive");
                }
            }
        }
        
        // Filter relations that match POS verbs with similarity ≥ 0.3
        List<String> filteredRelations = new ArrayList<>();
        List<String> filteredPolarities = new ArrayList<>();
        
        for (int i = 0; i < relations.size(); i++) {
            String relationVerb = relations.get(i);
            boolean matched = false;
            for (String posVerb : pos_verbs) {
                double similarity = jw.apply(relationVerb.toLowerCase(), posVerb.toLowerCase());
                if (similarity >= 0.3 && !matched) {
                    filteredRelations.add(relationVerb);
                    filteredPolarities.add(extractedPolarities.get(i));
                    matched = true; // Prevent duplicate additions
                }
            }
        }
        
        if (filteredRelations.isEmpty()) {
            return 1.0;
        }
        
        double sum = 0.0;
        double polarityPenalty = 0.0;
        
        if (filteredRelations.size() > pos_verbs.size()) {
            // Match each POS verb to best relation
            for (String posVerb : pos_verbs) {
                double maxSimilarity = 0.0;
                int bestMatch = -1;
                
                for (int i = 0; i < filteredRelations.size(); i++) {
                    String relationVerb = filteredRelations.get(i);
                    double similarity = jw.apply(relationVerb.toLowerCase(), posVerb.toLowerCase());
                    if (similarity > maxSimilarity) {
                        maxSimilarity = similarity;
                        bestMatch = i;
                    }
                }
                
                sum += (1.0 - maxSimilarity);
                
                // Add polarity penalty if there's a mismatch
                if (bestMatch != -1) {
                    String extractedPolarity = filteredPolarities.get(bestMatch);
                    // Find corresponding ideal polarity (simplified matching by verb similarity)
                    String idealPolarity = findBestMatchingIdealPolarity(posVerb, idealRelations, idealPolarities);
                    if (!extractedPolarity.equals(idealPolarity)) {
                        polarityPenalty += lambda;
                    }
                }
            }
        } else {
            // Match each relation to best POS verb
            for (int i = 0; i < filteredRelations.size(); i++) {
                String relationVerb = filteredRelations.get(i);
                double maxSimilarity = 0.0;
                String bestPosVerb = "";
                
                for (String posVerb : pos_verbs) {
                    double similarity = jw.apply(relationVerb.toLowerCase(), posVerb.toLowerCase());
                    if (similarity > maxSimilarity) {
                        maxSimilarity = similarity;
                        bestPosVerb = posVerb;
                    }
                }
                
                sum += (1.0 - maxSimilarity);
                
                // Add polarity penalty if there's a mismatch
                if (!bestPosVerb.isEmpty()) {
                    String extractedPolarity = filteredPolarities.get(i);
                    String idealPolarity = findBestMatchingIdealPolarity(bestPosVerb, idealRelations, idealPolarities);
                    if (!extractedPolarity.equals(idealPolarity)) {
                        polarityPenalty += lambda;
                    }
                }
            }
        }
        
        if (pos_verbs.size() > filteredRelations.size()) {
            sum += Math.abs(pos_verbs.size() - filteredRelations.size());
        }
        
        sum = sum / (2 * pos_verbs.size());
        
        // Add normalized polarity penalty
        double normalizedPolarityPenalty = polarityPenalty / pos_verbs.size();
        
        return Math.min(1.0, sum + normalizedPolarityPenalty); // Ensure result stays within [0, 1]
    }
    
    /**
     * Helper method to find the best matching ideal polarity for a given POS verb.
     */
    static String findBestMatchingIdealPolarity(String posVerb, List<String> idealRelations, List<String> idealPolarities) {
        double maxSimilarity = 0.0;
        String bestPolarity = "positive"; // default
        
        for (int i = 0; i < idealRelations.size(); i++) {
            double similarity = jw.apply(posVerb.toLowerCase(), idealRelations.get(i).toLowerCase());
            if (similarity > maxSimilarity && i < idealPolarities.size()) {
                maxSimilarity = similarity;
                bestPolarity = idealPolarities.get(i);
            }
        }
        
        return bestPolarity;
    }
    
    /**
     * Helper method to get expected polarity for a POS verb from polarity-enhanced triples.
     */
    static String getExpectedPolarity(JSONObject polarityTriples, int sentenceNumber, String posVerb) {
        try {
            if (polarityTriples.containsKey(String.valueOf(sentenceNumber))) {
                List<List<String>> triples = (List<List<String>>) polarityTriples.get(String.valueOf(sentenceNumber));
                
                double maxSimilarity = 0.0;
                String bestPolarity = "positive";
                
                for (List<String> triple : triples) {
                    if (triple.size() >= 4) {
                        String predicate = triple.get(1);
                        String polarity = triple.get(3);
                        
                        double similarity = jw.apply(posVerb.toLowerCase(), predicate.toLowerCase());
                        if (similarity > maxSimilarity) {
                            maxSimilarity = similarity;
                            bestPolarity = polarity;
                        }
                    }
                }
                
                return bestPolarity;
            }
        } catch (Exception e) {
            // Fall back to default
        }
        
        return "positive"; // default
    }

    public static void main(String[] args) {

        // String[] oieTools= new String[5];
        // String[] oieOutput=new String[5];
        // String[] oiePredicateOutput=new String[5];
        // oieOutput[0]="clausie_output.txt";
        // oieOutput[1]="stanford_4.5.3_openie_output.txt";
        // oieOutput[2]="stanford_4.5.6_openie_output.txt";
        // oieOutput[3]="minie_output.txt";
        // oieOutput[4]="ollie_output.txt";
        // oiePredicateOutput[0]="clausie_predicate_output.txt";
        // oiePredicateOutput[1]="stanford_4.5.3_openie_predicate_output.txt";
        // oiePredicateOutput[2]="stanford_4.5.6_openie_predicate_output.txt";
        // oiePredicateOutput[3]="minie_predicate_output.txt";
        // oiePredicateOutput[4]="ollie_predicate_output.txt";
        // oieTools[0]="triple_clauseie.json";
        // oieTools[1]="stanford_4.5.3_openie.json";
        // oieTools[2]="stanford_4.5.6_openie.json";
        // oieTools[3]="triple_minie.json";
        // oieTools[4]="triple_ollie.json";


        String[] oieTools= new String[1];
        String[] oieOutput=new String[1];
        String[] oiePredicateOutput=new String[1];
        oieOutput[0]="ideal_tinybutmighty.txt";
        // oieOutput[1]="gemini.txt";
        // oieOutput[2]="gpt4o.txt";
        // oieOutput[3]="minie.txt";
        // oieOutput[4]="ollie.txt";
    
        oiePredicateOutput[0]="ideal_tinybutmighty.txt";
        // oiePredicateOutput[1]="gemini.txt";
        // oiePredicateOutput[2]="gpt4o.txt";
        // oiePredicateOutput[3]="minie.txt";
        // oiePredicateOutput[4]="ollie.txt";

        oieTools[0]="tinybutmighty.json";
        // oieTools[1]="gemini2.5pro.json";
        // oieTools[2]="GPT-4o-mini.json";
        // oieTools[3]="triple_minie.json";
        // oieTools[4]="triple_ollie.json";
        


        JSONParser parser = new JSONParser();


        //subject and object

        for(int tool = 0;tool<1;tool++){
            double finalsum=0;
                try {
            Object obj = parser.parse(new FileReader("Json_Ideal/"+oieTools[tool]));
            JSONObject triples = (JSONObject) obj;
            try(BufferedWriter writer = new BufferedWriter(new FileWriter("output_ideal_tinybutmighty/"+oieOutput[tool]))){

                for(int targetSentenceNumber =1;targetSentenceNumber<=720;targetSentenceNumber++)
                {
                    if(triples.containsKey(String.valueOf(targetSentenceNumber))){
                        // List of created graphs
                        List<Graph> graphs = new ArrayList<>();

                        // Read lines from output_pos.txt and store them in a list
                        List<String> pos = new ArrayList<>();
                        BufferedReader br = new BufferedReader(new FileReader("output_pos_ideal_tinybutmighty.txt"));
                        // BufferedReader br = new BufferedReader(new FileReader("somewetaoutput.txt"));
                        String line;
                        int lineNumber = 0;
                        while ((line = br.readLine()) != null) {

                            if (lineNumber == targetSentenceNumber - 1) {
                                // Split the line into individual elements
                                String[] elements = line.replaceAll("\\[|\\]", "").split(",\\s*");
                                
                                // Add each element to the list
                                for (String element : elements) {
                                    pos.add(element.trim());
                                }
                                
                                break; // Stop reading after finding the target line
                            }

                            lineNumber++;
                        }

                        // Retrieve the values corresponding to targetSentenceNumber
                        List<List<String>> newinputStrings = new ArrayList<>();
                        if (triples != null && triples.containsKey(String.valueOf(targetSentenceNumber))) {
                            newinputStrings = (List<List<String>>) triples.get(String.valueOf(targetSentenceNumber));
                        }

                        List<List<String>> inputStrings = new ArrayList<>();

                        for (List<String> innerList : newinputStrings) {
                            List<String> newList = new ArrayList<>(innerList);
                            inputStrings.add(newList);
                        }
                        
                        // Map for storing the similarity score//
                        Map<String, Double> noun_similarity_score = new HashMap<>();

                        // Processing input strings
                        for (List<String> tuple : inputStrings) {
                            
                            String node1 = tuple.get(0);
                            String relation = tuple.get(1);
                            String node2 = tuple.get(2);

                            List<String> nodeList1 = new ArrayList<>();
                            List<String> nodeList2 = new ArrayList<>();

                            
                            // Find matching elements in pos list for node1
                            int word_checked_subject=0;
                            for (String word : pos) {
                                if (node1.toLowerCase().contains(word.toLowerCase())) {
                                    word_checked_subject=1;
                                    nodeList1.add(word);
                                    if (!noun_similarity_score.containsKey(word)) {
                                        noun_similarity_score.put(word, 1.0);
                                    }
                                }
                            }

                            if (word_checked_subject == 0) {
                                double maxSimilarity = 0.0;
                                String bestMatch = "";

                                for (String word : pos) {
                                    double similarity = jw.apply(node1.toLowerCase(), word.toLowerCase());
                                    if (similarity > maxSimilarity) {
                                        maxSimilarity = similarity;
                                        bestMatch = word;
                                    }
                                }

                                // Only add if similarity is more than 50%
                                if (maxSimilarity >= 0.3 && !bestMatch.isEmpty()) {
                                    nodeList1.add(bestMatch);
                                    if (!noun_similarity_score.containsKey(bestMatch)) {
                                        noun_similarity_score.put(bestMatch, maxSimilarity);
                                    }
                                }
                            }

                            



                            // Find matching elements in pos list for node2
                            int word_checked_object = 0;

                            for (String word : pos) {
                                if (node2.toLowerCase().contains(word.toLowerCase())) {
                                    word_checked_object = 1;
                                    nodeList2.add(word);
                                    if (!noun_similarity_score.containsKey(word)) {
                                        noun_similarity_score.put(word, 1.0);
                                    }
                                }
                            }

                            if (word_checked_object == 0) {
                                double maxSimilarity = 0.0;
                                String bestMatch = "";

                                for (String word : pos) {
                                    double similarity = jw.apply(node2.toLowerCase(), word.toLowerCase());
                                    if (similarity > maxSimilarity) {
                                        maxSimilarity = similarity;
                                        bestMatch = word;
                                    }
                                }

                                if (maxSimilarity >= 0.3 && !bestMatch.isEmpty()) {
                                    nodeList2.add(bestMatch);
                                    if (!noun_similarity_score.containsKey(bestMatch)) {
                                        noun_similarity_score.put(bestMatch, maxSimilarity);
                                    }
                                }
                            }



                            boolean edgeExistsInAllGraphs = true;
                            for (Graph graph : graphs) {
                                if (!graph.edgeExists(nodeList1, nodeList2)) {
                                    edgeExistsInAllGraphs = false;
                                    break;
                                }
                            }

                            if (edgeExistsInAllGraphs) {
                                Graph newGraph = new Graph();
                                newGraph.addEdge(nodeList1, nodeList2);
                                graphs.add(newGraph);
                            } else {
                                for (Graph graph : graphs) {
                                    if (!graph.edgeExists(nodeList1, nodeList2)) {
                                        graph.addEdge(nodeList1, nodeList2);
                                        break;
                                    }
                                }
                            }
                        }

                        // Printing details of each graph
                        int[] posElementCounts = new int[graphs.size()];

                        for (int i = 0; i < graphs.size(); i++) {
                            Graph graph = graphs.get(i);
                            // System.out.println("Graph-" + (i + 1));
                            // // graph.printGraph();
                            // System.out.println("Number of nodes: " + graph.numberOfNodes());
                            // System.out.println("Number of components: " + graph.numberOfComponents());
                            // System.out.println();

                            // Count pos elements in the graph
                            posElementCounts[i] = graph.countPosElements();

                            // Print all ArrayList of nodes
                            // System.out.println("ArrayList of nodes in Graph-" + (i + 1) + ":");
                            // for (String key : graph.nodes.keySet()) {
                            //     List<String> values = graph.nodes.get(key).values;
                            //     System.out.println("Node [" + String.join(", ", values) + "]");
                            // }
                            // System.out.println();

                            // Collect all pos elements present in the graph nodes
                            // Set<String> posElements = graph.collectPosElements();
                            // System.out.println("All pos elements in Graph-" + (i + 1) + ": " + posElements);
                            // System.out.println();
                        }

                        // Print array of pos element counts
                        // System.out.println("Number of pos elements in each graph:");
                        // for (int i = 0; i < posElementCounts.length; i++) {
                        //     System.out.println("Graph-" + (i + 1) + ": " + posElementCounts[i]);
                        // }

                        // Calculate and print the metric sum
                        // double finalsum=0;
                        double sum = 0;
                        double noun_sum=0;
                        for (int i = 0; i < graphs.size(); i++) {
                            noun_sum += posElementCounts[i];
                        }
                        for (int i = 0; i < graphs.size(); i++) {
                            sum += calculate_d(graphs.get(i), pos.size(), posElementCounts[i],noun_sum, noun_similarity_score);
                        }
                        // System.out.println("sum- :"+ sum);

                        // if(String.valueOf(sum).equals("Infinity")){
                        //     sum=0.0;
                        // }
                        
                        writer.write(targetSentenceNumber +" "+ sum/(2*pos.size()) + "\n");

                        finalsum+=sum/(2*pos.size());

                    }
                    else{

                        List<String> pos = new ArrayList<>();
                        BufferedReader br = new BufferedReader(new FileReader("output_pos_ideal_tinybutmighty.txt"));
                        // BufferedReader br = new BufferedReader(new FileReader("somewetaoutput.txt"));
                        String line;
                        int lineNumber = 0;
                        while ((line = br.readLine()) != null) {

                            if (lineNumber == targetSentenceNumber - 1) {
                                // Split the line into individual elements
                                String[] elements = line.replaceAll("\\[|\\]", "").split(",\\s*");
                                
                                // Add each element to the list
                                for (String element : elements) {
                                    pos.add(element.trim());
                                }
                                
                                break; // Stop reading after finding the target line
                            }

                            lineNumber++;
                        }

                        double sum = 2*pos.size();
                        writer.write(targetSentenceNumber +" "+ sum/(2*pos.size()) + "\n");

                        finalsum+=sum/(2*pos.size());

                    }

                }
                writer.write("\n"+"Avg. value is: " + finalsum/720.0+ "\n");

            }
            }
            catch (Exception e) 
            {
                e.printStackTrace();
            }
    }


        //predicate - intrinsic evaluation against POS verbs with polarity support
        for (int tool = 0; tool < 1; tool++) {
            double finalsum = 0.0;
            try {
                Object obj = parser.parse(new FileReader("Json_Ideal/" + oieTools[tool]));
                JSONObject triples = (JSONObject) obj;
                
                // Load polarity information for sentences
                Object polarityObj = null;
                JSONObject polarityTriples = new JSONObject();
                try {
                    polarityObj = parser.parse(new FileReader("Json_Ideal_Polarity/" + oieTools[tool]));
                    polarityTriples = (JSONObject) polarityObj;
                } catch (Exception e) {
                    System.out.println("Warning: Could not load polarity data, using intrinsic evaluation only");
                }

                new File("output_predicate_ideal_tinybutmighty").mkdirs();
                try (BufferedWriter writer = new BufferedWriter(new FileWriter("output_predicate_ideal_tinybutmighty/" + oiePredicateOutput[tool]))) {

                    for (int targetSentenceNumber = 1; targetSentenceNumber <= 720; targetSentenceNumber++) {
                        double sum = 0.0;

                        // Get POS verbs from output_verbs.txt
                        List<String> pos_verbs = new ArrayList<>();
                        try (BufferedReader br = new BufferedReader(new FileReader("output_verbs_ideal_tinybutmighty.txt"))) {
                            String line;
                            int lineNumber = 0;
                            while ((line = br.readLine()) != null) {
                                if (lineNumber == targetSentenceNumber - 1) {
                                    String[] elements = line.replaceAll("\\[|\\]", "").split(",\\s*");
                                    for (String element : elements) {
                                        if (!element.trim().isEmpty()) {
                                            pos_verbs.add(element.trim());
                                        }
                                    }
                                    break;
                                }
                                lineNumber++;
                            }
                        }

                        // INTRINSIC EVALUATION: Compare extracted relations against POS verbs
                        List<String> relations = new ArrayList<>();
                        List<String> extractedPolarities = new ArrayList<>();
                        
                        if (triples.containsKey(String.valueOf(targetSentenceNumber))) {
                            List<List<String>> newinputStrings = (List<List<String>>) triples.get(String.valueOf(targetSentenceNumber));
                            
                            // Extract relations and polarities from triples
                            for (List<String> tuple : newinputStrings) {
                                if (tuple.size() > 1) {
                                    relations.add(tuple.get(1)); // relation is at index 1
                                    
                                    // Get polarity if available (4-tuple), otherwise default
                                    if (tuple.size() >= 4) {
                                        extractedPolarities.add(tuple.get(3));
                                    } else {
                                        extractedPolarities.add("positive"); // default
                                    }
                                }
                            }

                            // Filter out relations that do not match any POS verb with sim ≥ 0.3
                            List<String> filteredRelations = new ArrayList<>();
                            List<String> filteredPolarities = new ArrayList<>();
                            
                            for (int i = 0; i < relations.size(); i++) {
                                String relationVerb = relations.get(i);
                                boolean matched = false;
                                for (String posVerb : pos_verbs) {
                                    double similarity = jw.apply(relationVerb.toLowerCase(), posVerb.toLowerCase());
                                    if (similarity >= 0.3 && !matched) {
                                        filteredRelations.add(relationVerb);
                                        filteredPolarities.add(extractedPolarities.get(i));
                                        matched = true; // keep only once per relation
                                    }
                                }
                            }

                            if (filteredRelations.isEmpty()) {
                                sum = 1.0;
                            } else {
                                double similaritySum = 0.0;
                                double polarityPenalty = 0.0;
                                double lambda = 0.1; // polarity penalty weight
                                
                                if (filteredRelations.size() > pos_verbs.size()) {
                                    // Match each POS verb to best relation
                                    for (String posVerb : pos_verbs) {
                                        double maxSimilarity = 0.0;
                                        int bestMatch = -1;
                                        
                                        for (int i = 0; i < filteredRelations.size(); i++) {
                                            String relationVerb = filteredRelations.get(i);
                                            double similarity = jw.apply(relationVerb.toLowerCase(), posVerb.toLowerCase());
                                            if (similarity > maxSimilarity) {
                                                maxSimilarity = similarity;
                                                bestMatch = i;
                                            }
                                        }
                                        
                                        similaritySum += (1.0 - maxSimilarity);
                                        
                                        // Add polarity penalty if polarities available
                                        if (bestMatch != -1 && !polarityTriples.isEmpty()) {
                                            String extractedPolarity = filteredPolarities.get(bestMatch);
                                            // Get expected polarity from polarity-enhanced triples
                                            String expectedPolarity = getExpectedPolarity(polarityTriples, targetSentenceNumber, posVerb);
                                            if (!extractedPolarity.equals(expectedPolarity)) {
                                                polarityPenalty += lambda;
                                            }
                                        }
                                    }
                                } else {
                                    // Match each relation to best POS verb
                                    for (int i = 0; i < filteredRelations.size(); i++) {
                                        String relationVerb = filteredRelations.get(i);
                                        double maxSimilarity = 0.0;
                                        String bestPosVerb = "";
                                        
                                        for (String posVerb : pos_verbs) {
                                            double similarity = jw.apply(relationVerb.toLowerCase(), posVerb.toLowerCase());
                                            if (similarity > maxSimilarity) {
                                                maxSimilarity = similarity;
                                                bestPosVerb = posVerb;
                                            }
                                        }
                                        
                                        similaritySum += (1.0 - maxSimilarity);
                                        
                                        // Add polarity penalty if polarities available
                                        if (!bestPosVerb.isEmpty() && !polarityTriples.isEmpty()) {
                                            String extractedPolarity = filteredPolarities.get(i);
                                            String expectedPolarity = getExpectedPolarity(polarityTriples, targetSentenceNumber, bestPosVerb);
                                            if (!extractedPolarity.equals(expectedPolarity)) {
                                                polarityPenalty += lambda;
                                            }
                                        }
                                    }
                                }
                                
                                // Add penalty for missing verbs
                                if (pos_verbs.size() > filteredRelations.size()) {
                                    similaritySum += Math.abs(pos_verbs.size() - filteredRelations.size());
                                }
                                
                                // Normalize and add polarity penalty
                                sum = (similaritySum / (2 * pos_verbs.size())) + (polarityPenalty / pos_verbs.size());
                                sum = Math.min(1.0, sum); // Ensure result stays within [0, 1]
                            }

                        } else {
                            sum = 1.0; // no relations case
                        }

                        writer.write(targetSentenceNumber + " " + sum + "\n");
                        finalsum += sum;
                    }

                    writer.write("\nAvg. value is: " + finalsum / 720.0 + "\n");

                } catch (Exception e) {
                    e.printStackTrace();
                }

            } catch (Exception e) {
                e.printStackTrace();
            }
        }
        
        // Combined metric calculation
        double alpha = 0.5; // weight for noun vs predicate metrics
        new File("output_combined_ideal_tinybutmighty").mkdirs();
        
        try (BufferedReader nounReader = new BufferedReader(new FileReader("output_ideal_tinybutmighty/ideal_tinybutmighty.txt"));
             BufferedReader predReader = new BufferedReader(new FileReader("output_predicate_ideal_tinybutmighty/ideal_tinybutmighty.txt"));
             BufferedWriter combinedWriter = new BufferedWriter(new FileWriter("output_combined_ideal_tinybutmighty/combined_metric.txt"))) {
            
            String nounLine, predLine;
            double combinedSum = 0.0;
            int count = 0;
            
            while ((nounLine = nounReader.readLine()) != null && (predLine = predReader.readLine()) != null) {
                if (!nounLine.startsWith("Avg.") && !predLine.startsWith("Avg.") && 
                    !nounLine.trim().isEmpty() && !predLine.trim().isEmpty()) {
                    
                    String[] nounParts = nounLine.split(" ");
                    String[] predParts = predLine.split(" ");
                    
                    if (nounParts.length >= 2 && predParts.length >= 2) {
                        int sentenceNum = Integer.parseInt(nounParts[0]);
                        double nounMetric = Double.parseDouble(nounParts[1]);
                        double predMetric = Double.parseDouble(predParts[1]);
                        
                        double combinedMetric = alpha * nounMetric + (1.0 - alpha) * predMetric;
                        
                        combinedWriter.write(sentenceNum + " " + combinedMetric + "\n");
                        combinedSum += combinedMetric;
                        count++;
                    }
                }
            }
            
            combinedWriter.write("\nAvg. combined metric: " + combinedSum / count + "\n");
            
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}