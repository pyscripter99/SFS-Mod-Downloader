import flet as ft
import time, random
from pocketbase import PocketBase
import requests, os

DEBUG = True
DB_URL = "https://moddown.thelocal.cf" if not DEBUG else "http://127.0.0.1:8090"
SFS_PATH = "C:/Program Files (x86)/Steam/steamapps/common/Spaceflight Simulator/Spaceflight Simulator Game"

client = PocketBase(DB_URL)


class mod_view(ft.UserControl):
    def __init__(
        self,
        mod_name: str,
        mod_versions: dict,
        type_="mod",
        summery=None,
        dependencies=[],
    ):
        super().__init__()
        self.mod_name = mod_name
        self.mod_versions = mod_versions
        self.type_ = type_
        self.summery = summery
        self.dependencies = dependencies

    def delete_done(self):
        self.pr_ring.visible = False
        self.remove_btn.visible = False
        self.download_btn.visible = True
        self.update()

    def download_done(self):
        self.download_btn.visible = False
        self.pr_ring.visible = False
        self.remove_btn.visible = True
        self.update()

    def download_clicked(self, e):
        self.download_btn.visible = False
        self.remove_btn.visible = False
        self.pr_ring.visible = True
        self.update()
        time.sleep(1)
        self.pr_ring.value = 0
        for x in range(20):
            time.sleep(3 / 20 + random.randint(0, 100) / 1000)
            self.pr_ring.value += 1 / 20
            self.update()
        self.pr_ring.value = None
        self.download_done()

    def delete_clicked(self, e):
        self.remove_btn.visible = False
        self.download_btn.visible = False
        self.pr_ring.visible = True
        self.update()
        time.sleep(1)
        self.delete_done()

    def ver_drop_change(self, e):
        self.dep_text.value = "Loading Dependencies..."
        self.dep_ring.visible = True
        self.dep_text.update()
        self.dep_ring.update()
        ver = client.collection("mod_version").get_one(self.ver_drop.value)
        self.dependencies = []
        for dep in ver.dependencies:
            dep_mod = client.collection("mod_version").get_one(dep)
            dep_mod_mod = client.collection("mods").get_one(dep_mod.mod)
            self.dependencies.append(dep_mod_mod.mod_name)
        self.dep_text.value = (
            ("Dependencies: " + ", ".join(self.dependencies))
            if len(self.dependencies) > 0
            else ""
        )
        self.dep_ring.visible = False
        self.dep_ring.update()
        self.dep_text.update()

    def build(self):
        self.pr_ring = ft.ProgressRing(width=20, height=20, visible=False)
        self.download_btn = ft.IconButton(
            ft.icons.DOWNLOAD,
            icon_color=ft.colors.GREEN,
            icon_size=25,
            on_click=self.download_clicked,
        )
        self.remove_btn = ft.IconButton(
            ft.icons.DELETE,
            icon_color=ft.colors.RED,
            icon_size=25,
            on_click=self.delete_clicked,
            visible=False,
        )

        self.options = []
        for k, v in self.mod_versions.items():
            self.options.append(ft.dropdown.Option(k, v))

        self.ver_drop = ft.Dropdown(
            options=self.options,
            height=60,
            width=200,
            prefix_text="v",
            text_style=ft.TextStyle(14),
        )

        self.ver_drop.on_change = self.ver_drop_change
        # self.dependencies = ["T1", "t2", "t3", "t4", "t5"]
        self.dep_text = ft.Text(
            "Dependencies: "
            + (
                ", ".join(self.dependencies[:4])
                + (
                    f", and {len(self.dependencies) - 4} other{'s' if len(self.dependencies) - 4 > 1 else ''}"
                    if len(self.dependencies) > 4
                    else ""
                )
                if self.dependencies
                else ""
            ),
            color=ft.colors.GREY,
        )

        self.dep_ring = ft.ProgressRing(visible=False, width=15, height=15)

        return ft.Row(
            [
                ft.Row(
                    [
                        ft.Column(
                            [
                                ft.Text(self.mod_name, size=20, width=200),
                                ft.Text(self.summery, size=14, color=ft.colors.GREY),
                            ],
                            spacing=1,
                        ),
                        self.ver_drop,
                    ]
                ),
                ft.Row(
                    [
                        self.dep_ring,
                        self.dep_text,
                    ]
                ),
                ft.Stack([self.download_btn, self.pr_ring, self.remove_btn], width=40),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

    def update(self):
        global list_filter
        if self.type_ in list_filter:
            self.visible = True
        else:
            self.visible = False
        return super().update()


def add_mod(mod):
    global mods_view, list_filter
    versions = (
        client.collection("mod_version")
        .get_list(query_params={"filter": 'mod = "' + mod.id + '"', "sort": "-version"})
        .items
    )
    versions_dict = {}
    for ver in versions:
        versions_dict[ver.id] = ver.version
    mod_v = mod_view(mod.mod_name, versions_dict, mod.type, mod.summery)
    mod_v.visible = True if mod.type in list_filter else False
    mods_view.controls.append(mod_v)
    mods_view.update()


def update_mods(control):
    for c in control.controls:
        if type(c) == mod_view:
            c.update()
        try:
            update_mods(c)
        except:
            pass


def filter_change(e, page: ft.Page):
    global list_filter, ck_mod, ck_parts, ck_text
    list_filter = []
    if ck_mod.value:
        list_filter.append("mod")
    if ck_parts.value:
        list_filter.append("parts")
    if ck_text.value:
        list_filter.append("textures")
    update_mods(page)
    page.update()


def main(page: ft.Page):
    page.theme_mode = ft.ThemeMode.DARK
    page.title = "SFS Mod Downloader"
    page.horizontal_alignment = ft.MainAxisAlignment.CENTER

    global list_filter, ck_mod, ck_parts, ck_text
    list_filter = ["mod"]
    ck_mod = ft.Checkbox(
        label="Mods", value=True, on_change=lambda e: filter_change(e, page)
    )
    ck_parts = ft.Checkbox(
        label="Part Packs", value=False, on_change=lambda e: filter_change(e, page)
    )
    ck_text = ft.Checkbox(
        label="Texture Packs", value=False, on_change=lambda e: filter_change(e, page)
    )

    page.add(ft.Row([ck_mod, ck_parts, ck_text]))

    global mods_view
    mods_view = ft.ListView(auto_scroll=False, spacing=10, divider_thickness=1)
    page.add(mods_view)

    mods = (
        client.collection("mods")
        .get_list(query_params={"sort": "-mod_name", "filter": 'type = "mod"'})
        .items
    )
    for mod in mods:
        add_mod(mod)


ft.app(target=main)
