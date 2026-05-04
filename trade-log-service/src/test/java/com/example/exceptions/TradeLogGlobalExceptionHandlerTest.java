package com.example.exceptions;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

import org.junit.jupiter.api.Test;
import org.mockito.Mockito;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.test.web.servlet.MockMvc;

import com.example.controllers.LogController;
import com.example.dto.AccountDTO;
import com.example.dto.EnrichedTrade;
import com.example.service.LogProducer;
import com.fasterxml.jackson.databind.ObjectMapper;

@WebMvcTest(LogController.class)
@AutoConfigureMockMvc(addFilters = false)
class TradeLogGlobalExceptionHandlerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private LogProducer producer;

    private ObjectMapper objectMapper = new ObjectMapper();

    private EnrichedTrade validTrade() {
        AccountDTO buyer = new AccountDTO();
        buyer.setAccountNumber("B1");
        buyer.setHolderName("Buyer");

        AccountDTO seller = new AccountDTO();
        seller.setAccountNumber("S1");
        seller.setHolderName("Seller");

        EnrichedTrade trade = new EnrichedTrade();
        trade.setTradeId("T1");
        trade.setAmount(100.0);
        trade.setBuyerAccount("B1");
        trade.setSellerAccount("S1");
        trade.setTime("10:30");
        trade.setBuyerAccountDetails(buyer);
        trade.setSellerAccountDetails(seller);
        return trade;
    }

    // ========== 400 InvalidTradeException ==========

    @Test
    void testHandleInvalidTrade() throws Exception {
        Mockito.doThrow(new InvalidTradeException("Buyer account details cannot be null"))
                .when(producer).sendLog(Mockito.any());

        mockMvc.perform(post("/log/trade")
                        .contentType("application/json")
                        .content(objectMapper.writeValueAsString(validTrade())))
                .andExpect(status().isBadRequest())
                .andExpect(content().string("Buyer account details cannot be null"));
    }

    // ========== 400 InvalidXmlException ==========

    @Test
    void testHandleInvalidXml() throws Exception {
        Mockito.doThrow(new InvalidXmlException("Malformed XML"))
                .when(producer).sendLog(Mockito.any());

        mockMvc.perform(post("/log/trade")
                        .contentType("application/json")
                        .content(objectMapper.writeValueAsString(validTrade())))
                .andExpect(status().isBadRequest())
                .andExpect(content().string("Malformed XML"));
    }

    // ========== 500 Generic Exception ==========

    @Test
    void testHandleGenericException() throws Exception {
        Mockito.doThrow(new RuntimeException("Unexpected error"))
                .when(producer).sendLog(Mockito.any());

        mockMvc.perform(post("/log/trade")
                        .contentType("application/json")
                        .content(objectMapper.writeValueAsString(validTrade())))
                .andExpect(status().isInternalServerError())
                .andExpect(content().string("Unexpected error"));
    }

    // ========== GET health endpoint ==========

    @Test
    void testHealthEndpoint() throws Exception {
        mockMvc.perform(get("/log"))
                .andExpect(status().isOk())
                .andExpect(content().string("hi"));
    }
}
