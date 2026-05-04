package com.example.demo.services;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import com.example.consumers.TradeConsumer;
import com.example.entities.Trade;
import com.example.exceptions.InvalidXmlException;
import com.example.services.TradeService;
import com.fasterxml.jackson.dataformat.xml.XmlMapper;

@ExtendWith(MockitoExtension.class)
class TradeConsumerTest {

    @InjectMocks
    private TradeConsumer tradeConsumer;

    @Mock
    private TradeService tradeService;

    private String validXml() {
        return "<Trade>" +
                "<tradeId>T1</tradeId>" +
                "<time>10:30</time>" +
                "<amount>5000</amount>" +
                "<buyerAccount>123</buyerAccount>" +
                "<sellerAccount>456</sellerAccount>" +
                "</Trade>";
    }

    // ========== SUCCESS ==========

    @Test
    void testConsume_Success() throws Exception {
        doNothing().when(tradeService).process(validXml());

        tradeConsumer.consume(validXml());

        verify(tradeService, times(1)).process(validXml());
    }

    // ========== INVALID XML — should catch InvalidXmlException and NOT rethrow ==========

    @Test
    void testConsume_InvalidXml_Skipped() {
        String badXml = "<bad>xml</bad>";

        doThrow(new InvalidXmlException("Invalid XML"))
                .when(tradeService).process(badXml);

        // Should NOT throw — InvalidXmlException is caught and skipped
        assertDoesNotThrow(() -> tradeConsumer.consume(badXml));

        verify(tradeService, times(1)).process(badXml);
    }

    // ========== GENERIC EXCEPTION — should be rethrown for Kafka retry ==========

    @Test
    void testConsume_GenericException_Rethrown() {
        String xml = validXml();

        doThrow(new RuntimeException("Service down"))
                .when(tradeService).process(xml);

        // Should rethrow — Kafka will retry
        assertThrows(RuntimeException.class, () -> tradeConsumer.consume(xml));
    }

    // ========== DLT HANDLER ==========

    @Test
    void testHandleDlt() {
        String failedXml = validXml();
        Exception ex = new RuntimeException("All retries exhausted");

        // Should not throw — just logs
        assertDoesNotThrow(() -> tradeConsumer.handleDlt(failedXml, ex));
    }

    // ========== XML PARSING (unit test for Trade entity) ==========

    @Test
    void testXmlParsing_AllFields() throws Exception {
        XmlMapper mapper = new XmlMapper();
        Trade trade = mapper.readValue(validXml(), Trade.class);

        assertEquals("T1", trade.getTradeId());
        assertEquals("10:30", trade.getTime());
        assertEquals(5000.0, trade.getAmount());
        assertEquals("123", trade.getBuyerAccount());
        assertEquals("456", trade.getSellerAccount());
    }

    @Test
    void testXmlParsing_SettersWork() {
        Trade trade = new Trade();
        trade.setTradeId("T99");
        trade.setTime("11:00");
        trade.setAmount(9999.0);
        trade.setBuyerAccount("B1");
        trade.setSellerAccount("S1");

        assertEquals("T99", trade.getTradeId());
        assertEquals("11:00", trade.getTime());
        assertEquals(9999.0, trade.getAmount());
        assertEquals("B1", trade.getBuyerAccount());
        assertEquals("S1", trade.getSellerAccount());
    }

    @Test
    void testTrade_ParameterizedConstructor() {
        Trade trade = new Trade("B1", "S1", 100.0, "12:00", "T1");

        assertEquals("T1", trade.getTradeId());
        assertEquals("12:00", trade.getTime());
        assertEquals(100.0, trade.getAmount());
        assertEquals("B1", trade.getBuyerAccount());
        assertEquals("S1", trade.getSellerAccount());
    }
}