package com.pmq.vnnewsvoice.auth.mapper;

import com.pmq.vnnewsvoice.auth.dto.NotificationDto;
import com.pmq.vnnewsvoice.auth.pojo.Notification;
import org.mapstruct.Mapper;
import org.mapstruct.Mapping;

@Mapper(componentModel = "spring")
public interface NotificationMapper {
  @Mapping(target = "userId", source = "userId.id")
  NotificationDto toDto(Notification notification);
}
