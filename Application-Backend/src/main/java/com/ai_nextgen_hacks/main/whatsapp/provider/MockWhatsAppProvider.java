package com.ai_nextgen_hacks.main.whatsapp.provider;
import com.ai_nextgen_hacks.main.whatsapp.dto.SendWhatsAppMessageResponse;
import org.springframework.stereotype.Component;
import java.util.UUID;

@Component("mockWhatsAppProvider")
public class MockWhatsAppProvider implements WhatsAppProvider {
    @Override
    public SendWhatsAppMessageResponse sendMessage(String phoneNumber, String message) {
        System.out.println("MOCK WHATSAPP: Sending to " + phoneNumber + ": " + message);
        return new SendWhatsAppMessageResponse("SENT", getProviderName(), "mock-" + UUID.randomUUID().toString());
    }
    @Override
    public String getProviderName() { return "MOCK"; }
}
