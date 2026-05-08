package com.example.services;

import java.math.BigDecimal;

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

    @Autowired
    private AmountTruncationService amountTruncationService;


    private final XmlMapper xmlMapper = new XmlMapper();
    private final ObjectMapper objectMapper = new ObjectMapper();

    public void process(String xml) throws Exception {

        System.out.println("RAW XML = " + xml);

        Trade trade;

        // XML parsing
        try {
            trade = xmlMapper.readValue(xml, Trade.class);
        } catch (Exception ex) {
            throw new InvalidXmlException("Invalid XML");
        }

        // Fetch accounts
        AccountDTO partyAccount1 = accountClient.getAccount(trade.getPartyAccount1());
        AccountDTO partyAccount2 = accountClient.getAccount(trade.getPartyAccount2());
        System.out.println(" Party Account 1 = " + partyAccount1);
        System.out.println(" Party Account 2 = " + partyAccount2);

        if (partyAccount1 == null || partyAccount2 == null) {
            System.out.println(" Skipping → account not found");
            throw new Exception("Account not found");
        }
        BigDecimal amount = amountTruncationService.truncateToTwoDecimalPlaces(trade.getAmount());
        // Enrich
        EnrichedTrade enriched = new EnrichedTrade(
                trade.getTradeId(),
                trade.getTime(),
                amount,
                trade.getPartyAccount1(),
                trade.getPartyAccount2(),
                partyAccount1,
                partyAccount2
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