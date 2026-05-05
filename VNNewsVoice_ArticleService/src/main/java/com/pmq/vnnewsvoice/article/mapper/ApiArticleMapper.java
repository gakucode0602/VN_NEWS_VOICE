package com.pmq.vnnewsvoice.article.mapper;

import com.pmq.vnnewsvoice.article.dto.ArticleResponse;
import com.pmq.vnnewsvoice.article.pojo.Article;
import org.mapstruct.Mapper;
import org.mapstruct.Mapping;

@Mapper(componentModel = "spring")
public abstract class ApiArticleMapper {

  @Mapping(target = "generatorIdId", source = "generatorId.id")
  @Mapping(target = "generatorIdName", source = "generatorId.name")
  @Mapping(target = "generatorIdLogoUrl", source = "generatorId.logoUrl")
  @Mapping(target = "generatorIdUrl", source = "generatorId.url")
  @Mapping(target = "categoryIdId", source = "categoryId.id")
  @Mapping(target = "categoryIdName", source = "categoryId.name")
  // commentCount left null — CommentService is in a separate microservice
  @Mapping(target = "commentCount", ignore = true)
  public abstract ArticleResponse toResponse(Article article);
}
