import { CloudServerOutlined, PlusOutlined, SaveOutlined } from "@ant-design/icons";
import {
    Alert,
    Button,
    Card,
    Empty,
    Input,
    List,
    Segmented,
    Select,
    Space,
    Spin,
    Switch,
    Tag,
    Typography,
    message,
} from "antd";
import { useEffect, useMemo, useState } from "react";
import { useTheme } from "../../app/ThemeContext";
import { useSettings } from "../../app/SettingsContext";
import { discoverProviderModels, testProviderConnection } from "../../services/settings";
import type {
    AppearanceSettings,
    ChatPreferenceSettings,
    CredentialStorageMode,
    DataPrivacySettings,
    LocalProviderProfile,
    ProviderProfile,
    ProviderType,
} from "../../types/settings";

type ProviderDraft = {
    profileId?: string;
    providerType: ProviderType;
    displayName: string;
    baseUrl: string;
    apiKey: string;
    modelName: string;
    storageMode: CredentialStorageMode;
    models: string[];
};

const providerTypeOptions = [
    { label: "默认云端", value: "carbonrag_cloud" },
    { label: "OpenAI 兼容", value: "openai_compatible" },
    { label: "Ollama", value: "ollama" },
    { label: "OpenAI", value: "openai" },
    { label: "Anthropic", value: "anthropic" },
    { label: "Gemini", value: "gemini" },
    { label: "DeepSeek", value: "deepseek" },
] as const;

function buildBlankProviderDraft(storageMode: CredentialStorageMode = "local_only"): ProviderDraft {
    return {
        providerType: storageMode === "local_only" ? "openai_compatible" : "openai_compatible",
        displayName: storageMode === "local_only" ? "我的本地模型" : "我的账号模型",
        baseUrl: "",
        apiKey: "",
        modelName: "",
        storageMode,
        models: [],
    };
}

export function SettingsPage() {
    const { themeMode, themePreset, allPresets, setThemeMode, setThemePreset } = useTheme();
    const {
        settings,
        providerList,
        localProfiles,
        loading,
        saveSettings,
        createAccountProviderProfile,
        updateAccountProviderProfile,
        deleteAccountProviderProfile,
        upsertLocalProfile,
        deleteLocalProfile,
    } = useSettings();
    const [transportError, setTransportError] = useState<string | null>(null);
    const [providerDraft, setProviderDraft] = useState<ProviderDraft>(() => buildBlankProviderDraft());
    const [testingProvider, setTestingProvider] = useState(false);
    const [savingProvider, setSavingProvider] = useState(false);

    const quickThemePresets = useMemo(() => allPresets.slice(0, 4), [allPresets]);
    const extendedThemePresets = useMemo(() => allPresets.slice(4), [allPresets]);

    useEffect(() => {
        if (!settings) {
            return;
        }
        setThemeMode(settings.appearance.theme_mode);
        setThemePreset(settings.appearance.theme_preset);
    }, [settings?.appearance.theme_mode, settings?.appearance.theme_preset]);

    async function handleSaveAppearance() {
        await handleSaveAppearanceDraft({
            ...settings!.appearance,
            theme_mode: themeMode,
            theme_preset: themePreset,
        }, true);
    }

    async function handleSaveAppearanceDraft(nextAppearance: AppearanceSettings, showSuccess = false) {
        try {
            setTransportError(null);
            await saveSettings({
                appearance: nextAppearance,
            });
            if (showSuccess) {
                message.success("外观设置已保存。");
            }
        } catch {
            setTransportError("当前无法保存外观设置。");
        }
    }

    function handleThemeModeChange(nextMode: typeof themeMode) {
        setThemeMode(nextMode);
        if (!settings) {
            return;
        }
        void handleSaveAppearanceDraft({
            ...settings.appearance,
            theme_mode: nextMode,
            theme_preset: themePreset,
        });
    }

    function handleThemePresetChange(nextPreset: typeof themePreset) {
        setThemePreset(nextPreset);
        if (!settings) {
            return;
        }
        void handleSaveAppearanceDraft({
            ...settings.appearance,
            theme_mode: themeMode,
            theme_preset: nextPreset,
        });
    }

    async function handleSaveChatSettings(partial: Partial<ChatPreferenceSettings>) {
        try {
            setTransportError(null);
            await saveSettings({
                chat: {
                    ...settings!.chat,
                    ...partial,
                },
            });
        } catch {
            setTransportError("当前无法保存聊天偏好。");
        }
    }

    async function handleSaveDataPrivacy(partial: Partial<DataPrivacySettings>) {
        try {
            setTransportError(null);
            await saveSettings({
                data_privacy: {
                    ...settings!.data_privacy,
                    ...partial,
                },
            });
        } catch {
            setTransportError("当前无法保存数据与隐私设置。");
        }
    }

    async function handleSetActiveProvider(providerRef: string) {
        try {
            setTransportError(null);
            await saveSettings({ active_provider_ref: providerRef });
            message.success("当前模型提供方已切换。");
        } catch {
            setTransportError("当前无法切换模型提供方。");
        }
    }

    async function handleDiscoverModels() {
        setTestingProvider(true);
        try {
            const result = await discoverProviderModels({
                provider_type: providerDraft.providerType,
                base_url: providerDraft.baseUrl || undefined,
                api_key: providerDraft.apiKey || undefined,
                model_name: providerDraft.modelName || undefined,
            });
            setProviderDraft((current) => ({
                ...current,
                baseUrl: result.normalized_base_url ?? current.baseUrl,
                models: result.models,
                modelName: current.modelName || result.models[0] || "",
            }));
            message.success("模型列表已刷新。");
        } catch {
            setTransportError("当前无法发现模型列表，请检查提供方配置。");
        } finally {
            setTestingProvider(false);
        }
    }

    async function handleTestProvider() {
        setTestingProvider(true);
        try {
            const result = await testProviderConnection({
                provider_type: providerDraft.providerType,
                base_url: providerDraft.baseUrl || undefined,
                api_key: providerDraft.apiKey || undefined,
                model_name: providerDraft.modelName || undefined,
            });
            if (result.ok) {
                message.success(result.message);
                if (result.discovered_models.length) {
                    setProviderDraft((current) => ({
                        ...current,
                        models: result.discovered_models,
                        modelName: current.modelName || result.discovered_models[0] || "",
                    }));
                }
            } else {
                setTransportError(result.message);
            }
        } catch {
            setTransportError("当前无法测试 provider 连接。");
        } finally {
            setTestingProvider(false);
        }
    }

    async function handleSaveProvider() {
        setSavingProvider(true);
        try {
            setTransportError(null);
            if (providerDraft.storageMode === "local_only") {
                const profileId = providerDraft.profileId ?? `local-${Date.now().toString(36)}`;
                await upsertLocalProfile({
                    profile_id: profileId,
                    provider_type: providerDraft.providerType,
                    display_name: providerDraft.displayName,
                    base_url: providerDraft.baseUrl || undefined,
                    api_key: providerDraft.apiKey || undefined,
                    model_name: providerDraft.modelName || undefined,
                    config_json: {},
                });
                await handleSetActiveProvider(`local:${profileId}`);
            } else {
                const payload = {
                    provider_type: providerDraft.providerType,
                    display_name: providerDraft.displayName,
                    base_url: providerDraft.baseUrl || undefined,
                    api_key: providerDraft.apiKey || undefined,
                    model_name: providerDraft.modelName || undefined,
                    config_json: {},
                    storage_mode: "account" as const,
                };
                let profileId = providerDraft.profileId;
                if (profileId) {
                    await updateAccountProviderProfile(profileId, payload);
                } else {
                    const created = await createAccountProviderProfile(payload);
                    profileId = created.profile_id;
                }
                await handleSetActiveProvider(`account:${profileId}`);
            }
            setProviderDraft(buildBlankProviderDraft(providerDraft.storageMode));
            message.success("Provider 配置已保存。");
        } catch {
            setTransportError("当前无法保存 provider 配置。");
        } finally {
            setSavingProvider(false);
        }
    }

    function editAccountProfile(profile: ProviderProfile) {
        setProviderDraft({
            profileId: profile.profile_id,
            providerType: profile.provider_type,
            displayName: profile.display_name,
            baseUrl: profile.base_url ?? "",
            apiKey: "",
            modelName: profile.model_name ?? "",
            storageMode: "account",
            models: [],
        });
    }

    function editLocalProfile(profile: LocalProviderProfile) {
        setProviderDraft({
            profileId: profile.profile_id,
            providerType: profile.provider_type,
            displayName: profile.display_name,
            baseUrl: profile.base_url ?? "",
            apiKey: profile.api_key ?? "",
            modelName: profile.model_name ?? "",
            storageMode: "local_only",
            models: [],
        });
    }

    if (loading || !settings || !providerList) {
        return (
            <div className="settings-page settings-page--loading">
                <Spin />
            </div>
        );
    }

    return (
        <div className="settings-page">
            {transportError ? <Alert type="warning" showIcon message={transportError} /> : null}

            <Card title="外观">
                <Space direction="vertical" size={16} style={{ width: "100%" }}>
                    <div>
                        <Typography.Text strong>主题模式</Typography.Text>
                        <Segmented
                            block
                            value={themeMode}
                            options={[
                                { label: "浅色", value: "light" },
                                { label: "暗色", value: "dark" },
                                { label: "跟随系统", value: "system" },
                            ]}
                            onChange={(value) => handleThemeModeChange(value as typeof themeMode)}
                        />
                    </div>
                    <div>
                        <Typography.Text strong>快速主题</Typography.Text>
                        <div className="settings-theme-grid">
                            {quickThemePresets.map((preset) => (
                                <button
                                    key={preset.id}
                                    type="button"
                                    className={preset.id === themePreset ? "theme-preset-card theme-preset-card--active" : "theme-preset-card"}
                                    onClick={() => handleThemePresetChange(preset.id)}
                                >
                                    <span className="theme-preset-card__swatches">
                                        {preset.preview.map((color, index) => (
                                            <span key={`${preset.id}-${index}`} className="theme-preset-card__swatch" style={{ background: color }} />
                                        ))}
                                    </span>
                                    <span className="theme-preset-card__copy">
                                        <Typography.Text strong>{preset.label}</Typography.Text>
                                        <Typography.Text type="secondary">{preset.description}</Typography.Text>
                                    </span>
                                </button>
                            ))}
                        </div>
                    </div>
                    <div>
                        <Typography.Text strong>更多主题</Typography.Text>
                        <div className="settings-theme-grid settings-theme-grid--extended">
                            {extendedThemePresets.map((preset) => (
                                <button
                                    key={preset.id}
                                    type="button"
                                    className={preset.id === themePreset ? "theme-preset-card theme-preset-card--active" : "theme-preset-card"}
                                    onClick={() => handleThemePresetChange(preset.id)}
                                >
                                    <span className="theme-preset-card__swatches">
                                        {preset.preview.map((color, index) => (
                                            <span key={`${preset.id}-${index}`} className="theme-preset-card__swatch" style={{ background: color }} />
                                        ))}
                                    </span>
                                    <span className="theme-preset-card__copy">
                                        <Typography.Text strong>{preset.label}</Typography.Text>
                                    </span>
                                </button>
                            ))}
                        </div>
                    </div>
                    <div>
                        <Typography.Text strong>气泡密度</Typography.Text>
                        <Segmented
                            block
                            value={settings.appearance.bubble_density}
                            options={[
                                { label: "舒适", value: "comfortable" },
                                { label: "紧凑", value: "compact" },
                            ]}
                            onChange={(value) => void saveSettings({
                                appearance: {
                                    ...settings.appearance,
                                    bubble_density: value as "comfortable" | "compact",
                                },
                            })}
                        />
                    </div>
                    <div>
                        <Typography.Text strong>字体大小</Typography.Text>
                        <Segmented
                            block
                            value={settings.appearance.font_size}
                            options={[
                                { label: "默认", value: "default" },
                                { label: "大号", value: "large" },
                            ]}
                            onChange={(value) => void saveSettings({
                                appearance: {
                                    ...settings.appearance,
                                    font_size: value as "default" | "large",
                                },
                            })}
                        />
                    </div>
                    <div>
                        <Typography.Text strong>侧栏默认状态</Typography.Text>
                        <Segmented
                            block
                            value={settings.appearance.sidebar_default}
                            options={[
                                { label: "默认展开", value: "expanded" },
                                { label: "默认收起", value: "collapsed" },
                            ]}
                            onChange={(value) => void saveSettings({
                                appearance: {
                                    ...settings.appearance,
                                    sidebar_default: value as "expanded" | "collapsed",
                                },
                            })}
                        />
                    </div>
                    <Button type="primary" icon={<SaveOutlined />} onClick={() => void handleSaveAppearance()}>
                        保存外观设置
                    </Button>
                </Space>
            </Card>

            <Card title="聊天">
                <Space direction="vertical" size={16} style={{ width: "100%" }}>
                    <div>
                        <Typography.Text strong>发送方式</Typography.Text>
                        <Segmented
                            block
                            value={settings.chat.send_shortcut}
                            options={[
                                { label: "Enter 发送", value: "enter" },
                                { label: "Ctrl+Enter 发送", value: "ctrl_enter" },
                            ]}
                            onChange={(value) => void handleSaveChatSettings({ send_shortcut: value as "enter" | "ctrl_enter" })}
                        />
                    </div>
                    <Space wrap>
                        <Switch checked={settings.chat.expand_thinking_by_default} onChange={(checked) => void handleSaveChatSettings({ expand_thinking_by_default: checked })} />
                        <Typography.Text>默认展开思考过程</Typography.Text>
                    </Space>
                    <Space wrap>
                        <Switch checked={settings.chat.show_evidence_panel_by_default} onChange={(checked) => void handleSaveChatSettings({ show_evidence_panel_by_default: checked })} />
                        <Typography.Text>默认显示依据面板</Typography.Text>
                    </Space>
                    <Space wrap>
                        <Switch checked={settings.chat.show_context_debug_by_default} onChange={(checked) => void handleSaveChatSettings({ show_context_debug_by_default: checked })} />
                        <Typography.Text>显示上下文调试信息</Typography.Text>
                    </Space>
                    <Space wrap>
                        <Switch checked={settings.chat.auto_generate_title_for_new_session} onChange={(checked) => void handleSaveChatSettings({ auto_generate_title_for_new_session: checked })} />
                        <Typography.Text>新会话自动生成标题</Typography.Text>
                    </Space>
                    <div>
                        <Typography.Text strong>重连提示显示方式</Typography.Text>
                        <Segmented
                            block
                            value={settings.chat.reconnect_notice_mode}
                            options={[
                                { label: "仅消息内提示", value: "message_only" },
                                { label: "消息内 + 弹出提示", value: "toast_and_message" },
                            ]}
                            onChange={(value) => void handleSaveChatSettings({
                                reconnect_notice_mode: value as "message_only" | "toast_and_message",
                            })}
                        />
                    </div>
                </Space>
            </Card>

            <Card title="模型与提供方" extra={<Tag color="blue">{settings.active_provider_ref}</Tag>}>
                <Space direction="vertical" size={16} style={{ width: "100%" }}>
                    <div className="settings-provider-toolbar">
                        <Button icon={<CloudServerOutlined />} onClick={() => void handleSetActiveProvider("builtin:carbonrag-cloud")}>
                            切回默认云端
                        </Button>
                        <Button icon={<PlusOutlined />} onClick={() => setProviderDraft(buildBlankProviderDraft("local_only"))}>
                            新建本地 Provider
                        </Button>
                        <Button icon={<PlusOutlined />} onClick={() => setProviderDraft(buildBlankProviderDraft("account"))}>
                            新建账号 Provider
                        </Button>
                    </div>

                    <div className="settings-provider-columns">
                        <Card size="small" title="当前可用 Provider">
                            <List
                                dataSource={[
                                    { key: "builtin:carbonrag-cloud", label: "CarbonRag 默认云端", type: "builtin" as const },
                                    ...providerList.profiles.map((item) => ({ key: `account:${item.profile_id}`, label: item.display_name, type: "account" as const, profile: item })),
                                    ...localProfiles.map((item) => ({ key: `local:${item.profile_id}`, label: item.display_name, type: "local" as const, profile: item })),
                                ]}
                                renderItem={(item) => (
                                    <List.Item
                                        actions={[
                                            <Button key="use" size="small" type={settings.active_provider_ref === item.key ? "primary" : "default"} onClick={() => void handleSetActiveProvider(item.key)}>
                                                启用
                                            </Button>,
                                            item.type === "account" ? (
                                                <Button key="edit" size="small" onClick={() => editAccountProfile(item.profile as ProviderProfile)}>编辑</Button>
                                            ) : null,
                                            item.type === "local" ? (
                                                <Button key="edit" size="small" onClick={() => editLocalProfile(item.profile as LocalProviderProfile)}>编辑</Button>
                                            ) : null,
                                            item.type === "account" ? (
                                                <Button key="delete" size="small" danger onClick={() => void deleteAccountProviderProfile((item.profile as ProviderProfile).profile_id)}>删除</Button>
                                            ) : null,
                                            item.type === "local" ? (
                                                <Button key="delete" size="small" danger onClick={() => void deleteLocalProfile((item.profile as LocalProviderProfile).profile_id)}>删除</Button>
                                            ) : null,
                                        ].filter(Boolean)}
                                    >
                                        <List.Item.Meta
                                            title={item.label}
                                            description={item.type === "builtin" ? "内置开箱即用" : item.key}
                                        />
                                    </List.Item>
                                )}
                            />
                        </Card>

                        <Card size="small" title="Provider 编辑器">
                            <Space direction="vertical" size={12} style={{ width: "100%" }}>
                                <Segmented
                                    block
                                    value={providerDraft.storageMode}
                                    options={[
                                        { label: "仅当前设备", value: "local_only" },
                                        { label: "保存到账号", value: "account" },
                                    ]}
                                    onChange={(value) => setProviderDraft((current) => ({ ...buildBlankProviderDraft(value as CredentialStorageMode), profileId: undefined }))}
                                />
                                <Select
                                    value={providerDraft.providerType}
                                    options={providerTypeOptions.map((item) => ({ value: item.value, label: item.label }))}
                                    onChange={(value) => setProviderDraft((current) => ({ ...current, providerType: value }))}
                                />
                                <Input value={providerDraft.displayName} placeholder="显示名称" onChange={(event) => setProviderDraft((current) => ({ ...current, displayName: event.target.value }))} />
                                <Input value={providerDraft.baseUrl} placeholder="Base URL（可选）" onChange={(event) => setProviderDraft((current) => ({ ...current, baseUrl: event.target.value }))} />
                                <Input.Password value={providerDraft.apiKey} placeholder="API Key（可选）" onChange={(event) => setProviderDraft((current) => ({ ...current, apiKey: event.target.value }))} />
                                <Space.Compact style={{ width: "100%" }}>
                                    <Select
                                        style={{ flex: 1 }}
                                        value={providerDraft.modelName || undefined}
                                        placeholder="选择模型或手动填写"
                                        options={providerDraft.models.map((item) => ({ label: item, value: item }))}
                                        onChange={(value) => setProviderDraft((current) => ({ ...current, modelName: value }))}
                                    />
                                    <Input
                                        style={{ flex: 1 }}
                                        value={providerDraft.modelName}
                                        placeholder="模型名"
                                        onChange={(event) => setProviderDraft((current) => ({ ...current, modelName: event.target.value }))}
                                    />
                                </Space.Compact>
                                <Space wrap>
                                    <Button loading={testingProvider} onClick={() => void handleDiscoverModels()}>刷新模型</Button>
                                    <Button loading={testingProvider} onClick={() => void handleTestProvider()}>测试连接</Button>
                                    <Button type="primary" loading={savingProvider} icon={<SaveOutlined />} onClick={() => void handleSaveProvider()}>
                                        保存 Provider
                                    </Button>
                                </Space>
                            </Space>
                        </Card>
                    </div>
                </Space>
            </Card>

            <Card title="数据与隐私">
                <Space direction="vertical" size={12}>
                    <Space wrap>
                        <Switch checked={settings.data_privacy.store_local_provider_keys_in_browser} onChange={(checked) => void handleSaveDataPrivacy({ store_local_provider_keys_in_browser: checked })} />
                        <Typography.Text>允许本地私有 Provider 凭据保存在浏览器中</Typography.Text>
                    </Space>
                    <Space wrap>
                        <Switch checked={settings.data_privacy.allow_account_saved_provider_keys} onChange={(checked) => void handleSaveDataPrivacy({ allow_account_saved_provider_keys: checked })} />
                        <Typography.Text>允许账号保存加密凭据</Typography.Text>
                    </Space>
                </Space>
            </Card>

            <Card title="高级">
                <Space direction="vertical" size={12} style={{ width: "100%" }}>
                    <Typography.Text type="secondary">
                        当前生效 Provider：{settings.active_provider_ref}
                    </Typography.Text>
                    {localProfiles.length ? (
                        <Typography.Text type="secondary">
                            当前设备已保存 {localProfiles.length} 个本地 Provider；其敏感 key 不会回传后端。
                        </Typography.Text>
                    ) : (
                        <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="当前还没有本地 Provider。" />
                    )}
                </Space>
            </Card>
        </div>
    );
}
