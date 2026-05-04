package com.example.clients;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.client.HttpClientErrorException;
import org.springframework.web.client.HttpServerErrorException;
import org.springframework.web.client.ResourceAccessException;
import org.springframework.web.client.RestTemplate;

import com.example.dto.AccountDTO;
import com.example.exceptions.RecoverableException;

@Component
public class AccountClient {

    @Value("${account.service.url}")
    private String accountUrl;

    private final RestTemplate restTemplate = new RestTemplate();

    public AccountDTO getAccount(String accountId) {

        System.out.println("Calling account service for: " + accountId);

        try {
            return restTemplate.getForObject(
                    accountUrl + accountId,
                    AccountDTO.class
            );

        } catch (ResourceAccessException ex) {
            throw new RecoverableException("Network issue (account service)", ex);

        } catch (HttpServerErrorException ex) {
            throw new RecoverableException("Server error (account service)", ex);

        } catch (HttpClientErrorException ex) {
            System.out.println("Account not found: " + accountId);
            return null;
        }
    }
}