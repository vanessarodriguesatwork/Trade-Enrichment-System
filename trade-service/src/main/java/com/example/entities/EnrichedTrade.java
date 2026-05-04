package com.example.entities;

import com.example.dto.AccountDTO;

public class EnrichedTrade {

    private String tradeId;
    private String time;
    private Double amount;
    private String buyerAccount;
    private String sellerAccount;
    private AccountDTO buyerAccountDetails;
    private AccountDTO sellerAccountDetails;
    
    public EnrichedTrade() {
    }

    public EnrichedTrade(String tradeId, String time, Double amount, String buyerAccount, String sellerAccount, AccountDTO buyerAccountDetails, AccountDTO sellerAccountDetails) {
        this.tradeId = tradeId;
        this.time = time;
        this.amount = amount;
        this.buyerAccount = buyerAccount;
        this.sellerAccount = sellerAccount;
        this.buyerAccountDetails = buyerAccountDetails;
        this.sellerAccountDetails = sellerAccountDetails;

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

    public AccountDTO getBuyerAccountDetails() {
        return buyerAccountDetails;
    }

    public void setBuyerAccountDetails(AccountDTO buyerAccountDetails) {
        this.buyerAccountDetails = buyerAccountDetails;
    }

    public AccountDTO getSellerAccountDetails() {
        return sellerAccountDetails;
    }

    public void setSellerAccountDetails(AccountDTO sellerAccountDetails) {
        this.sellerAccountDetails = sellerAccountDetails;
    }

    
}