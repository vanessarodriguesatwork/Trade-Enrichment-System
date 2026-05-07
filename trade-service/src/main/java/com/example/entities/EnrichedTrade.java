package com.example.entities;

import com.example.dto.AccountDTO;

public class EnrichedTrade {

    private String tradeId;
    private String time;
    private Double amount;
    private String partyAccount1;
    private String partyAccount2;
    private AccountDTO partyAccount1Details;
    private AccountDTO partyAccount2Details;
    private String buyerSellerIndicator;
    public EnrichedTrade() {
    }

    public EnrichedTrade(String tradeId, String time, Double amount, String partyAccount1, String partyAccount2, AccountDTO partyAccount1Details, AccountDTO partyAccount2Details, String buyerSellerIndicator) {
        this.tradeId = tradeId;
        this.time = time;
        this.amount = amount;
        this.partyAccount1 = partyAccount1;
        this.partyAccount2 = partyAccount2;
        this.partyAccount1Details = partyAccount1Details;
        this.partyAccount2Details = partyAccount2Details;
        this.buyerSellerIndicator = buyerSellerIndicator;
    }

    public String getTradeId() {
        return tradeId;
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

    public AccountDTO getPartyAccount1Details() {
        return partyAccount1Details;
    }

    public void setPartyAccount1Details(AccountDTO partyAccount1Details) {
        this.partyAccount1Details = partyAccount1Details;
    }

    public AccountDTO getPartyAccount2Details() {
        return partyAccount2Details;
    }

    public void setPartyAccount2Details(AccountDTO partyAccount2Details) {
        this.partyAccount2Details = partyAccount2Details;
    }
    public String getBuyerSellerIndicator() {
        return buyerSellerIndicator;
    }
    public void setBuyerSellerIndicator(String buyerSellerIndicator) {
        this.buyerSellerIndicator = buyerSellerIndicator;
    }
    
}