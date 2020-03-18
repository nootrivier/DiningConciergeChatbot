package com.example.demo;

import java.io.IOException;
import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;

import org.apache.http.HttpEntity;
import org.apache.http.HttpHost;
import org.apache.http.client.methods.CloseableHttpResponse;
import org.apache.http.client.methods.HttpGet;
import org.apache.http.impl.client.CloseableHttpClient;
import org.apache.http.impl.client.HttpClients;
import org.apache.http.util.EntityUtils;
import org.elasticsearch.action.index.IndexRequest;
import org.elasticsearch.action.index.IndexResponse;
import org.elasticsearch.action.search.SearchRequest;
import org.elasticsearch.action.search.SearchResponse;
import org.elasticsearch.client.RequestOptions;
import org.elasticsearch.client.RestClient;
import org.elasticsearch.client.RestHighLevelClient;
import org.elasticsearch.index.query.QueryBuilders;
import org.elasticsearch.search.builder.SearchSourceBuilder;

import com.amazonaws.auth.AWS4Signer;
import com.amazonaws.auth.AWSCredentialsProvider;
import com.amazonaws.auth.DefaultAWSCredentialsProviderChain;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

import software.amazon.awssdk.services.dynamodb.model.AttributeValue;
import java.util.*;
public class InsertRecords {
    private static final String serviceName = "es";
    private static final String region = "us-east-2";
    private static final String aesEndpoint = "https://search-diningconcierge-rawwf5iwcizbl6vi2li664aagi.us-east-2.es.amazonaws.com";
    static final AWSCredentialsProvider credentialsProvider = new DefaultAWSCredentialsProviderChain();

    public InsertRecords() {
        Map<String, AttributeValue> itemValues = new HashMap<String, AttributeValue>();
        ObjectMapper objectMapper = new ObjectMapper();
        HttpGet request = new HttpGet(
                "https://api.yelp.com/v3/businesses/search?location=Manhattan&limit=50&term=american");
        request.addHeader("Authorization",
                "Bearer ee1otUHsHAKkDQH7E28I4er15q1MZOSNbv0sRPkfBvlqNuncAvO3oZfjAd23-Bj_FrJKgR3OwXREN3tmGdVKZYzAw1qzlI9lRfU1-u9pgcDQXzpyUubBMD5FXLdIXnYx");
        DiningConciergeDB diningConciergeDB = new DiningConciergeDB();
        try (
            RestHighLevelClient client = aesClient();
            CloseableHttpClient httpClient = HttpClients.createDefault();
            CloseableHttpResponse response = httpClient.execute(request);
            ) {
            HttpEntity entity = response.getEntity();
            if (entity != null) {
                
                JsonNode jsonNode = objectMapper.readValue(EntityUtils.toString(response.getEntity()), JsonNode.class);
                JsonNode businesses = jsonNode.get("businesses"); 
                int total = businesses.size(); // be it all the restaurants that are in manhattan, and, say, korean cuisine
                int count = 0;
                while (total != count) {
                    itemValues.put("id", AttributeValue.builder().s(businesses.get(count).get("id").asText()).build());
                    itemValues.put("address",
                            AttributeValue.builder().s(businesses.get(count).get("location").toString()).build());
                    itemValues.put("business_id",
                            AttributeValue.builder().s(businesses.get(count).get("id").asText()).build());
                    itemValues.put("coordinates",
                            AttributeValue.builder().s(businesses.get(count).get("coordinates").toString()).build());
                    itemValues.put("name",
                            AttributeValue.builder().s(businesses.get(count).get("name").asText()).build());
                    itemValues.put("rating",
                            AttributeValue.builder().s(businesses.get(count).get("rating").asText()).build());
                    itemValues.put("review",
                            AttributeValue.builder().s(businesses.get(count).get("review_count").asText()).build());
                    itemValues.put("zipcode", AttributeValue.builder()
                            .s(businesses.get(count).get("location").get("zip_code").asText()).build());
                    itemValues.put("insertedAtTimestamp",
                            AttributeValue.builder().s(LocalDateTime.now().toString()).build());

                    
                    SearchSourceBuilder sourceBuilder = new SearchSourceBuilder();
                    sourceBuilder.query(QueryBuilders.matchQuery("Restaurant.restaurant_id",
                            businesses.get(count).get("id").asText()));
                    
                    SearchRequest searchRequest = new SearchRequest("restaurants");
                    searchRequest.source(sourceBuilder);
                    SearchResponse searchResponse = client.search(searchRequest, RequestOptions.DEFAULT);

                    if (searchResponse.getHits().getTotalHits().value == 0) {
                        Map<String, Object> document = new HashMap<String, Object>();
                        Map<String, Object> restaurant = new HashMap<String, Object>();
                        
                        restaurant.put("restaurant_id", businesses.get(count).get("id").asText());
                        restaurant.put("cuisine", "american");
                        document.put("Restaurant", restaurant);
                        IndexRequest request1 = new IndexRequest("restaurants");
                        request1.source(document);
                        IndexResponse indexResponse = client.index(request1, RequestOptions.DEFAULT);
                        System.out.println("response id: " + indexResponse.getId());
                    }

                    
                    if (!diningConciergeDB.search("business_id", businesses.get(count).get("id").asText())) {
                        diningConciergeDB.add(itemValues);
                    }
                    count++;
                }
                System.out.println("data insertion done");
            }
        } //try block ends
        catch (IOException e) {
            e.printStackTrace();
        }
    }

    public static RestHighLevelClient aesClient() {
        AWS4Signer signer = new AWS4Signer();
        signer.setServiceName(serviceName);
        signer.setRegionName(region);
        return new RestHighLevelClient(RestClient.builder(HttpHost.create(aesEndpoint)));
    }

    public static void main(String[] args) {
        new InsertRecords();
    }

}
