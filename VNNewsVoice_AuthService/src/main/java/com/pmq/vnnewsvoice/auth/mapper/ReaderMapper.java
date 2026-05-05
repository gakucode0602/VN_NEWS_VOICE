package com.pmq.vnnewsvoice.auth.mapper;

import com.pmq.vnnewsvoice.auth.dto.ReaderDto;
import com.pmq.vnnewsvoice.auth.pojo.Reader;
import com.pmq.vnnewsvoice.auth.pojo.UserProvider;
import com.pmq.vnnewsvoice.auth.service.UserProviderService;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.mapstruct.AfterMapping;
import org.mapstruct.Mapper;
import org.mapstruct.Mapping;
import org.mapstruct.MappingTarget;
import org.springframework.beans.factory.annotation.Autowired;

@Mapper(componentModel = "spring")
public abstract class ReaderMapper {
  @Autowired protected UserProviderService userProviderService;

  @Mapping(target = "userIdId", source = "userId.id")
  @Mapping(target = "userIdUsername", source = "userId.username")
  @Mapping(target = "userIdAvatarUrl", source = "userId.avatarUrl")
  @Mapping(target = "userIdEmail", source = "userId.email")
  @Mapping(target = "userIdBirthday", source = "userId.birthday")
  @Mapping(target = "userIdAddress", source = "userId.address")
  @Mapping(target = "userIdPhoneNumber", source = "userId.phoneNumber")
  @Mapping(target = "userIdGender", source = "userId.gender")
  @Mapping(target = "userIdAvatarPublicId", source = "userId.avatarPublicId")
  @Mapping(target = "userIdRoleIdId", source = "userId.roleId.id")
  @Mapping(target = "userIdRoleIdName", source = "userId.roleId.name")
  @Mapping(target = "userProviders", ignore = true)
  public abstract ReaderDto toDto(Reader reader);

  @AfterMapping
  protected void addUserProviders(Reader reader, @MappingTarget ReaderDto readerDto) {
    if (reader.getUserId() == null) {
      return;
    }
    List<UserProvider> userProviders =
        userProviderService.getUserProvidersByUserId(reader.getUserId().getId());
    if (userProviders != null && !userProviders.isEmpty()) {
      List<Map<String, String>> providers = new ArrayList<>();
      for (UserProvider provider : userProviders) {
        Map<String, String> providerInfo = new HashMap<>();
        providerInfo.put("providerId", provider.getProviderId());
        providerInfo.put("providerType", provider.getProviderType());
        providers.add(providerInfo);
      }
      readerDto.setUserProviders(providers);
    }
  }
}
