package com.example.controllers;

import com.example.dto.EnrichedTrade;
import com.example.service.LogProducer;
import com.fasterxml.jackson.databind.ObjectMapper;

import org.junit.jupiter.api.Test;
import org.mockito.Mockito;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.*;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.test.web.servlet.MockMvc;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@WebMvcTest(LogController.class)
@AutoConfigureMockMvc(addFilters = false)
class LogControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private LogProducer producer; // ✅ prevents Kafka loading

    private ObjectMapper objectMapper = new ObjectMapper();

    @Test
    void testGet() throws Exception {
        mockMvc.perform(get("/log"))
                .andExpect(status().isOk())
                .andExpect(content().string("hi"));
    }

    @Test
    void testLogTrade() throws Exception {

        EnrichedTrade trade = new EnrichedTrade();
        trade.setTradeId("T1003");
        trade.setAmount(9000.0);
        trade.setBuyerAccount("A101");
        trade.setSellerAccount("A102");
        trade.setTime("2026-03-27");

        Mockito.doNothing().when(producer).sendLog(Mockito.any());

        mockMvc.perform(post("/log/trade")
                        .contentType("application/json")
                        .content(objectMapper.writeValueAsString(trade)))
                .andExpect(status().isOk())
                .andExpect(content().string("Trade logged to Kafka!"));

        Mockito.verify(producer).sendLog(Mockito.any());
    }
}