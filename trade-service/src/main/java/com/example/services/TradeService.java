package com.example.services;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import com.example.clients.AccountClient;
import com.example.clients.LoggingClient;
import com.example.dto.AccountDTO;
import com.example.entities.EnrichedTrade;
import com.example.entities.Trade;
import com.example.exceptions.InvalidXmlException;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.dataformat.xml.XmlMapper;

@Service
public class TradeService {

    @Autowired
    private AccountClient accountClient;

    @Autowired
    private LoggingClient loggingClient;

    private final XmlMapper xmlMapper = new XmlMapper();
    private final ObjectMapper objectMapper = new ObjectMapper();

    public void process(String xml) throws Exception{

        System.out.println("RAW XML = " + xml);

        Trade trade;

        // XML parsing
        try {
            trade = xmlMapper.readValue(xml, Trade.class);
        } catch (Exception ex) {
            throw new InvalidXmlException("Invalid XML");
        }

        // Fetch accounts
        AccountDTO buyer = accountClient.getAccount(trade.getPartyAccount1());
        AccountDTO seller = accountClient.getAccount(trade.getPartyAccount2());
        System.out.println(" Buyer = " + buyer);
        System.out.println(" Seller = " + seller);

        if (buyer == null || seller == null) {
            System.out.println(" Skipping → account not found");
            throw new Exception("Account not found");
        }
        
        // Convert buyerSellerIndicator to abbreviated format
        String abbreviatedIndicator = abbreviateBuyerSellerIndicator(trade.getBuyerSellerIndicator());
        
        // Enrich
        EnrichedTrade enriched = new EnrichedTrade(
                trade.getTradeId(),
                trade.getTime(),
                trade.getAmount(),
                trade.getPartyAccount1(),
                trade.getPartyAccount2(),
                buyer,
                seller,
                abbreviatedIndicator
        );

        try {
            String pretty = objectMapper
                    .writerWithDefaultPrettyPrinter()
                    .writeValueAsString(enriched);

            System.out.println("ENRICHED TRADE = \n" + pretty);

        } catch (JsonProcessingException ex) {
            System.out.println("JSON serialization failed");
        }

        // Send to logging
        loggingClient.send(enriched);
    }

    /**
     * Converts buyerSellerIndicator from input format (BUYER/SELLER) to abbreviated format (B/S).
     * 
     * Conversion rules:
     * - BUYER → "B"
     * - SELLER → "S"
     * - null/empty → "B" (default to BUYER for backward compatibility)
     * - invalid value → "" (empty string, with warning logged)
     * 
     * @param value The input buyerSellerIndicator value
     * @return Abbreviated indicator (B, S, or empty string)
     */
    private String abbreviateBuyerSellerIndicator(String value) {
        if (value == null || value.trim().isEmpty()) {
            // Default to BUYER for backward compatibility
            return "B";
        }
        
        String upperValue = value.trim().toUpperCase();
        
        if ("BUYER".equals(upperValue)) {
            return "B";
        } else if ("SELLER".equals(upperValue)) {
            return "S";
        } else {
            // Invalid value - log warning and return empty string
            System.out.println("WARN: Invalid buyerSellerIndicator value: '" + value + "'. Expected BUYER or SELLER.");
            return "";
        }
    }
}