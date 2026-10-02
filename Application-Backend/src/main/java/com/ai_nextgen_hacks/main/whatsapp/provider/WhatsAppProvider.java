package com.ai_nextgen_hacks.main.whatsapp.provider;
import com.ai_nextgen_hacks.main.whatsapp.dto.SendWhatsAppMessageResponse;

public interface WhatsAppProvider {
    SendWhatsAppMessageResponse sendMessage(String phoneNumber, String message);
    String getProviderName();
}
