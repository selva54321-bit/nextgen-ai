package com.ai_nextgen_hacks.main.whatsapp.provider;
import com.ai_nextgen_hacks.main.whatsapp.config.WhatsAppProperties;
import com.ai_nextgen_hacks.main.whatsapp.dto.SendWhatsAppMessageResponse;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;
import org.springframework.http.*;
import java.util.Map;
import java.util.UUID;

@Component("metaWhatsAppProvider")
public class MetaWhatsAppProvider implements WhatsAppProvider {
    
    @Autowired private WhatsAppProperties props;
    @Autowired private RestTemplate restTemplate;

    @Override
    public SendWhatsAppMessageResponse sendMessage(String phoneNumber, String message) {
        if (props.getAccessToken() == null || props.getAccessToken().isEmpty()) {
            throw new IllegalStateException("Meta WhatsApp requires Access Token");
        }
        
        String url = "https://graph.facebook.com/" + props.getApiVersion() + "/" + props.getPhoneNumberId() + "/messages";
        
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        headers.setBearerAuth(props.getAccessToken());
        
        Map<String, Object> textObj = Map.of("preview_url", false, "body", message);
        Map<String, Object> body = Map.of(
            "messaging_product", "whatsapp",
            "recipient_type", "individual",
            "to", phoneNumber.replace("+", ""),
            "type", "text",
            "text", textObj
        );
        
        HttpEntity<Map<String, Object>> entity = new HttpEntity<>(body, headers);
        try {
            ResponseEntity<Map> response = restTemplate.postForEntity(url, entity, Map.class);
            if (response.getStatusCode().is2xxSuccessful() && response.getBody() != null) {
                // Parse message ID
                String msgId = "meta-" + UUID.randomUUID().toString(); // simplify parsing for now
                return new SendWhatsAppMessageResponse("SENT", getProviderName(), msgId);
            }
        } catch(Exception e) {
            System.err.println("Meta API Error: " + e.getMessage());
            return new SendWhatsAppMessageResponse("FAILED", getProviderName(), null);
        }
        return new SendWhatsAppMessageResponse("FAILED", getProviderName(), null);
    }

    @Override
    public String getProviderName() { return "META"; }
}
