package com.pmq.vnnewsvoice.article.mapper;

import com.pmq.vnnewsvoice.article.dto.AdminArticleResponse;
import com.pmq.vnnewsvoice.article.pojo.Article;
import org.mapstruct.Mapper;
import org.mapstruct.Mapping;

@Mapper(componentModel = "spring")
public interface AdminArticleMapper {

  @Mapping(
      target = "status",
      expression = "java(article.getStatus() != null ? article.getStatus().name() : null)")
  @Mapping(target = "categoryIdId", source = "categoryId.id")
  @Mapping(target = "categoryIdName", source = "categoryId.name")
  @Mapping(target = "generatorIdId", source = "generatorId.id")
  @Mapping(target = "generatorIdName", source = "generatorId.name")
  @Mapping(target = "generatorIdLogoUrl", source = "generatorId.logoUrl")
  @Mapping(target = "generatorIdUrl", source = "generatorId.url")
  AdminArticleResponse toResponse(Article article);
}
