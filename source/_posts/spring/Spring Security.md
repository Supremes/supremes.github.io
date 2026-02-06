---
title: Spring Security
date: 2026-01-29 21:38:55
tags: []
categories:
cover: https://cdn.jsdelivr.net/gh/Supremes/blog-images@master/imgs/cover.jpg
sticky:
hidden: false
updated: 2026-02-07 22:14
---
Spring security 作为 spring 提供的认证和授权框架，基于 filter 链式结构，处理不同的 filter 来应对认证和授权业务场景。
- 在 SpringBoot 2.X 中，通过 extends `WebSecurityConfigurerAdapter`, 进行配置
- 在 SpringBoot 3.X 中，则通过使用 `SecurityFilterChain` Bean

### Spring Security 在 Spring Boot 2 vs 3 的主要区别

1. **`WebSecurityConfigurerAdapter` 已被移除**

| Spring Boot 2. x                             | Spring Boot 3. x                 |
| -------------------------------------------- | -------------------------------- |
| 继承 `WebSecurityConfigurerAdapter`            | 使用 `SecurityFilterChain` Bean    |
| 重写 `configure(HttpSecurity)`                 | 定义 `@Bean SecurityFilterChain`   |
| 重写 `configure(AuthenticationManagerBuilder)` | 定义 `@Bean AuthenticationManager` |
2. **API 链式调用变化**

| Spring Boot 2. x | Spring Boot 3. x |
|---|---|
| `http.authorizeRequests()` | `http.authorizeHttpRequests()` |
| `antMatchers()` | `requestMatchers()` |
| `.and()` 链式调用 | 使用 Lambda DSL（Customizer） |

3. **您的代码迁移示例**

**Spring Boot 2. x (当前代码):**
```java
@Configuration
@EnableWebSecurity
public class WebSecurityConfig extends WebSecurityConfigurerAdapter {
    
    @Override
    protected void configure(HttpSecurity http) throws Exception {
        http.formLogin()
            .loginProcessingUrl("/users/login")
            .and()
            .authorizeRequests()
            .anyRequest().authenticated();
    }
}
```

**Spring Boot 3. x (新写法):**
```java
@Configuration
@EnableWebSecurity
public class WebSecurityConfig {
    
    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        http
            .formLogin(form -> form
                .loginProcessingUrl("/users/login")
                .successHandler(authenticationSuccessHandler)
                .failureHandler(authenticationFailureHandler)
            )
            .authorizeHttpRequests(auth -> auth
                .anyRequest().authenticated()
            )
            .csrf(csrf -> csrf.disable())
            .exceptionHandling(ex -> ex
                .authenticationEntryPoint(authenticationEntryPoint)
                .accessDeniedHandler(accessDeniedHandler)
            )
            .sessionManagement(session -> session
                .sessionCreationPolicy(SessionCreationPolicy.STATELESS)
            )
            .addFilterBefore(jwtAuthenticationTokenFilter, UsernamePasswordAuthenticationFilter.class);
        
        return http.build();
    }
    
    @Bean
    public AuthenticationManager authenticationManager(AuthenticationConfiguration config) throws Exception {
        return config.getAuthenticationManager();
    }
}
```

4. **其他重要变化**

| 变化点 | 说明 |
|---|---|
| 包名变更 | `javax.*` → `jakarta.*` |
| `@EnableGlobalMethodSecurity` | → `@EnableMethodSecurity` |
| `FilterSecurityInterceptor` | → `AuthorizationFilter` (新授权架构) |
| `AccessDecisionManager` | → `AuthorizationManager` (推荐) |
