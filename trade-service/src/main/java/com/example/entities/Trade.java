package com.example.entities;

import com.fasterxml.jackson.dataformat.xml.annotation.JacksonXmlRootElement;

@JacksonXmlRootElement(localName = "Trade")
public class Trade {

    private String tradeId;
    private String time;
    private Double amount;
    private String buyerAccount;
    private String sellerAccount;
    public Trade(String buyerAccount, String sellerAccount, Double amount, String time, String tradeId) {
        this.buyerAccount = buyerAccount;
        this.sellerAccount = sellerAccount;
        this.amount = amount;
        this.time = time;
        this.tradeId = tradeId;
    }
    public String getTradeId() {
        return tradeId;
    }
    public String getBuyerAccount() {
        return buyerAccount;
    }
    public void setBuyerAccount(String buyerAccount) {
        this.buyerAccount = buyerAccount;
    }
    public String getSellerAccount() {
        return sellerAccount;
    }
    public void setSellerAccount(String sellerAccount) {
        this.sellerAccount = sellerAccount;
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
    public Double getAmount() {
        return amount;
    }
    public void setAmount(Double amount) {
        this.amount = amount;
    }
    public Trade() {
    }
}