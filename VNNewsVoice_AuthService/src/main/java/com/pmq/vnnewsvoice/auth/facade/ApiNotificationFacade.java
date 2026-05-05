package com.pmq.vnnewsvoice.auth.facade;

import com.pmq.vnnewsvoice.auth.dto.ApiResult;
import com.pmq.vnnewsvoice.auth.dto.NotificationDto;
import com.pmq.vnnewsvoice.auth.pojo.CustomUserDetails;

public interface ApiNotificationFacade {
  ApiResult<NotificationDto> markAsRead(Long id, CustomUserDetails principal);

  ApiResult<Void> markAllAsRead(CustomUserDetails principal);

  ApiResult<Long> getUnreadCount(CustomUserDetails principal);
}
