package com.example.demo;

import java.util.Map;
import java.util.Set;

import software.amazon.awssdk.regions.Region;
import software.amazon.awssdk.services.dynamodb.DynamoDbClient;
import software.amazon.awssdk.services.dynamodb.model.AttributeValue;
import software.amazon.awssdk.services.dynamodb.model.DynamoDbException;
import software.amazon.awssdk.services.dynamodb.model.PutItemRequest;
import software.amazon.awssdk.services.dynamodb.model.ResourceNotFoundException;
import software.amazon.awssdk.services.dynamodb.model.ScanRequest;
import software.amazon.awssdk.services.dynamodb.model.ScanResponse;

public class DiningConciergeDB {
    private String tableName = "yelp-restaurants";
    private Region region = Region.US_EAST_2;
    private DynamoDbClient ddb = null;

    public DiningConciergeDB() {
        ddb = DynamoDbClient.builder().region(region).build();
    }

    public boolean search(String key, String keyVal) {
        try {
            ScanRequest scanRequest = ScanRequest.builder().tableName(tableName).build();
            ScanResponse response = ddb.scan(scanRequest);
            for (Map<String, AttributeValue> item : response.items()) {
                Set<String> keys = item.keySet();
                for (String key1 : keys) {
                    if (key.equals(key1) && keyVal.equals(item.get(key1).s())) {
                        return true;
                    }
                }
            }
        } catch (DynamoDbException e) {
            e.printStackTrace();
        }
        return false;
    }

    public void add(Map<String, AttributeValue> itemValues) {
        PutItemRequest request = PutItemRequest.builder().tableName(tableName).item(itemValues).build();
        try {
            ddb.putItem(request);
            System.out.println(tableName + " was successfully updated");

        } catch (ResourceNotFoundException e) {
            System.err.format("Error: The table \"%s\" can't be found.\n", tableName);
            System.err.println("Be sure that it exists and that you've typed its name correctly!");
            System.exit(1);
        } catch (DynamoDbException e) {
            System.err.println(e.getMessage());
            System.exit(1);
        }
    }

    public static void main(String[] args) {
        new DiningConciergeDB();
    }

}
