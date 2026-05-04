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

    public void process(String xml) {

        System.out.println("RAW XML = " + xml);

        Trade trade;

        // XML parsing
        try {
            trade = xmlMapper.readValue(xml, Trade.class);
        } catch (Exception ex) {
            throw new InvalidXmlException("Invalid XML");
        }

        // Fetch accounts
        AccountDTO buyer = accountClient.getAccount(trade.getBuyerAccount());
        AccountDTO seller = accountClient.getAccount(trade.getSellerAccount());
        System.out.println(" Buyer = " + buyer);
        System.out.println(" Seller = " + seller);

        if (buyer == null || seller == null) {
            System.out.println(" Skipping → account not found");
            return;
        }
        // Enrich
        EnrichedTrade enriched = new EnrichedTrade(
                trade.getTradeId(),
                trade.getTime(),
                trade.getAmount(),
                trade.getBuyerAccount(),
                trade.getSellerAccount(),
                buyer,
                seller
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
}