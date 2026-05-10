package com.example.entities;

import com.fasterxml.jackson.dataformat.xml.annotation.JacksonXmlRootElement;

@JacksonXmlRootElement(localName = "Trade")
public class Trade {

    private String tradeId;
    private String time;
    private String amount;
    private String partyAccount1;
    private String partyAccount2;
    private String buyerSellerIndicator;
    public Trade(String partyAccount1, String partyAccount2, String amount, String time, String tradeId, String buyerSellerIndicator) {
        this.partyAccount1 = partyAccount1;
        this.partyAccount2 = partyAccount2;
        this.amount = amount;
        this.time = time;
        this.tradeId = tradeId;
        this.buyerSellerIndicator = buyerSellerIndicator;
    }
    public String getTradeId() {
        return tradeId;
    }
    public String getPartyAccount1() {
        return partyAccount1;
    }
    public void setPartyAccount1(String partyAccount1) {
        this.partyAccount1 = partyAccount1;
    }
    public String getPartyAccount2() {
        return partyAccount2;
    }
    public void setPartyAccount2(String partyAccount2) {
        this.partyAccount2 = partyAccount2;
    }
    public void setTradeId(String tradeId) {
        this.tradeId = tradeId;
    }
    public String getTime() {
        return time;
    }
    public void setTime(String time) {
        this.time = time;
    }
    public String getAmount() {
        return amount;
    }
    public void setAmount(String amount) {
        this.amount = amount;
    }
    public Trade() {
    }
    public String getBuyerSellerIndicator() {
        return buyerSellerIndicator;
    }
    public void setBuyerSellerIndicator(String buyerSellerIndicator) {
        this.buyerSellerIndicator = buyerSellerIndicator;
    }
}