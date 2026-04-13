import os, math, random, time, tempfile, wave, struct
from math import sin, cos, pi, radians
from direct.showbase.ShowBase import ShowBase
from direct.gui.OnscreenText import OnscreenText
from direct.task import Task
from panda3d.core import *
from direct.filter.CommonFilters import CommonFilters

# --- AYARLAR ---
loadPrcFileData("", "\n".join([
    "win-size 1280 720",
    "window-title TEVFİK İLERİ AİHL - UFKA KANAT ",
    "framebuffer-multisample 1",
    "multisamples 8",
    "textures-power-2 none",
    "shadow-depth-bits 24",
    "pstats-gpu-timing 1"
]))


class GeoFactory:
    @staticmethod
    def make_river(length=40000, width=150):
        # Nehir için düz bir zemin oluşturur
        cm = CardMaker("river_geom")
        cm.setFrame(-width / 2, width / 2, -length / 2, length / 2)
        node = cm.generate()
        river_np = NodePath(node)
        river_np.setHpr(0, -90, 0)  # Yatay yatır
        river_np.setColor(0, 0.4, 0.8, 0.8)  # Şeffafımsı mavi
        river_np.setTransparency(TransparencyAttrib.MAlpha)
        return river_np

    @staticmethod
    def make_mountain(height=150, width=300, col=Vec4(0.35, 0.4, 0.35, 1)):
        node = GeomNode("mountain")
        fmt = GeomVertexFormat.getV3n3c4()
        vdata = GeomVertexData("mountain", fmt, Geom.UHStatic)
        vtx, nrm, clr = (GeomVertexWriter(vdata, a) for a in ("vertex", "normal", "color"))
        tris = GeomTriangles(Geom.UHStatic)
        vtx.addData3f(0, 0, height);
        nrm.addData3f(0, 0, 1);
        clr.addData4f(col)
        pts = [(-width, -width, 0), (width, -width, 0), (width, width, 0), (-width, width, 0)]
        for p in pts:
            vtx.addData3f(*p);
            nrm.addData3f(0, 0, -1);
            clr.addData4f(col * 0.7)
        for i in range(1, 4): tris.addVertices(0, i, i + 1)
        tris.addVertices(0, 4, 1)
        geom = Geom(vdata);
        geom.addPrimitive(tris);
        node.addGeom(geom)
        return NodePath(node)

    @staticmethod
    def make_tree_leaves(size=12, col=Vec4(0.05, 0.35, 0.05, 1)):
        node = GeomNode("leaves")
        fmt = GeomVertexFormat.getV3n3c4()
        vdata = GeomVertexData("leaves", fmt, Geom.UHStatic)
        vtx, nrm, clr = (GeomVertexWriter(vdata, a) for a in ("vertex", "normal", "color"))
        tris = GeomTriangles(Geom.UHStatic)
        vtx.addData3f(0, 0, size);
        nrm.addData3f(0, 0, 1);
        clr.addData4f(col)
        w = size * 0.6
        pts = [(-w, -w, 0), (w, -w, 0), (w, w, 0), (-w, w, 0)]
        for p in pts:
            vtx.addData3f(*p);
            nrm.addData3f(0, 0, -1);
            clr.addData4f(col * 0.8)
        for i in range(1, 4): tris.addVertices(0, i, i + 1)
        tris.addVertices(0, 4, 1)
        geom = Geom(vdata);
        geom.addPrimitive(tris);
        node.addGeom(geom)
        return NodePath(node)

    @staticmethod
    def make_ring(r=6.5, h=1.8, seg=64, col=Vec4(1, 0.8, 0, 1), thick=0.8):
        fmt = GeomVertexFormat.getV3n3c4()
        vdata = GeomVertexData("ring", fmt, Geom.UHStatic)
        vtx, nrm, clr = (GeomVertexWriter(vdata, a) for a in ("vertex", "normal", "color"))
        tris = GeomTriangles(Geom.UHStatic)
        in_r, out_r = r - thick / 2, r + thick / 2
        for z in [-h / 2, h / 2]:
            for i in range(seg + 1):
                ang = i / seg * 2 * pi
                c, s = cos(ang), sin(ang)
                vtx.addData3f(out_r * c, out_r * s, z);
                nrm.addData3f(c, s, 0);
                clr.addData4f(col)
                vtx.addData3f(in_r * c, in_r * s, z);
                nrm.addData3f(-c, -s, 0);
                clr.addData4f(col)
        pts = (seg + 1) * 2
        for i in range(seg):
            b_o1, b_i1 = i * 2, i * 2 + 1
            b_o2, b_i2 = (i + 1) * 2, (i + 1) * 2 + 1
            t_o1, t_i1 = b_o1 + pts, b_i1 + pts
            t_o2, t_i2 = b_o2 + pts, b_i2 + pts
            tris.addVertices(b_o1, t_o2, t_o1);
            tris.addVertices(b_o1, b_o2, t_o2)
            tris.addVertices(b_i1, t_i1, t_i2);
            tris.addVertices(b_i1, t_i2, b_i2)
            tris.addVertices(t_o1, t_i2, t_i1);
            tris.addVertices(t_o1, t_o2, t_i2)
            tris.addVertices(b_o1, b_i1, b_i2);
            tris.addVertices(b_o1, b_i2, b_o2)
        geom = Geom(vdata);
        geom.addPrimitive(tris);
        node = GeomNode("ring");
        node.addGeom(geom)
        return NodePath(node)

    @staticmethod
    def make_box(size=Vec3(1, 1, 1), col=Vec4(1, 1, 1, 1)):
        node = GeomNode("box")
        vdata = GeomVertexData("box", GeomVertexFormat.getV3n3c4(), Geom.UHStatic)
        vtx, nrm, clr = (GeomVertexWriter(vdata, a) for a in ("vertex", "normal", "color"))
        tris = GeomTriangles(Geom.UHStatic)
        p = [(-.5, -.5, -.5), (.5, -.5, -.5), (.5, .5, -.5), (-.5, .5, -.5), (-.5, -.5, .5), (.5, -.5, .5),
             (.5, .5, .5), (-.5, .5, .5)]
        f = [(0, 1, 2, 3, (0, 0, -1)), (4, 5, 6, 7, (0, 0, 1)), (0, 1, 5, 4, (0, -1, 0)), (2, 3, 7, 6, (0, 1, 0)),
             (1, 2, 6, 5, (1, 0, 0)), (0, 3, 7, 4, (-1, 0, 0))]
        for a, b, c, d, n in f:
            for x, y, z in (p[a], p[b], p[c], p[d]):
                vtx.addData3f(x * size.x, y * size.y, z * size.z);
                nrm.addData3f(*n);
                clr.addData4f(col)
            curr = vtx.getWriteRow() - 4
            tris.addVertices(curr, curr + 1, curr + 2);
            tris.addVertices(curr, curr + 2, curr + 3)
        geom = Geom(vdata);
        geom.addPrimitive(tris);
        node.addGeom(geom)
        return NodePath(node)

    @staticmethod
    def create_sound_synthesis(freq=180, duration=2.5):
        temp_path = os.path.join(tempfile.gettempdir(), "drone_engine.wav")
        sr = 44100
        frames = int(duration * sr)
        with wave.open(temp_path, "wb") as w:
            w.setnchannels(1);
            w.setsampwidth(2);
            w.setframerate(sr)
            for i in range(frames):
                s = sin(2 * pi * freq * i / sr) * 0.7
                s += sin(2 * pi * (freq * 2.15) * i / sr) * 0.2
                noise = (random.random() * 2 - 1) * 0.05
                sample = int((s + noise) * 32767 * 0.3)
                w.writeframesraw(struct.pack("<h", sample))
        return temp_path


class UfkaKanatV5(ShowBase):
    def __init__(self):
        super().__init__()
        self.render.setShaderAuto()
        self.disableMouse()
        self.high_score = self.load_score()
        self.points, self.battery, self.shop_points = 0, 100.0, 0
        self.is_playing, self.is_shop_open = False, False
        self.keys = {}
        self.up_speed, self.up_battery, self.up_turn = 1.0, 1.0, 1.0
        self.pos, self.vel, self.hpr = Vec3(0, 0, 10), Vec3(0, 0, 0), Vec3(0, 0, 0)

        self.setup_filters()
        self.setup_environment()
        self.setup_drone()
        self.setup_ui()
        self.setup_controls()
        self.setup_audio()
        self.taskMgr.add(self.master_loop, "master_loop")

    def setup_filters(self):
        self.filters = CommonFilters(self.win, self.cam)
        self.filters.setBloom(intensity=1.2, desat=0.3, size="medium")

    def load_score(self):
        try:
            with open("highscore.txt", "r") as f:
                return int(f.read())
        except:
            return 0

    def setup_environment(self):
        self.camLens.setFar(200000)
        self.setBackgroundColor(0.5, 0.8, 1.0)

        fog = Fog("SceneFog")
        fog.setColor(0.65, 0.85, 0.7)
        fog.setLinearRange(2000, 15000)
        self.render.setFog(fog)

        al = AmbientLight("al")
        al.setColor((0.5, 0.5, 0.6, 1))
        self.render.setLight(self.render.attachNewNode(al))

        dl = DirectionalLight("dl")
        dl.setColor((1, 1, 0.95, 1))
        dln = self.render.attachNewNode(dl)
        dln.setHpr(45, -45, 0)
        self.render.setLight(dln)

        cm = CardMaker("ground")
        cm.setFrame(-50000, 50000, -50000, 50000)
        self.ground = self.render.attachNewNode(cm.generate())
        self.ground.setHpr(0, -90, 0)

        img = PNMImage(512, 512, 3)
        for x in range(512):
            for y in range(512):
                img.setXel(x, y, 0.15, 0.35 + random.random() * 0.05, 0.15)
        tex = Texture();
        tex.load(img)
        self.ground.setTexture(tex)
        self.ground.setTexScale(TextureStage.getDefault(), 1000, 1000)

        # --- NEHİR EKLEME ---
        self.river = GeoFactory.make_river()
        self.river.reparentTo(self.render)
        self.river.setPos(150, 0, 0.2)  # Zeminin hemen üzerinde
        # Nehir için akıntı dokusu
        river_img = PNMImage(256, 256, 3)
        for x in range(256):
            for y in range(256):
                river_img.setXel(x, y, 0.0, 0.3, 0.7 + random.random() * 0.3)
        self.river_tex = Texture()
        self.river_tex.load(river_img)
        self.river.setTexture(self.river_tex)
        self.river.setTexScale(TextureStage.getDefault(), 1, 50)

        # --- GELİŞTİRİLMİŞ İSTASYON (TEKO HUB V2) ---
        self.station = self.render.attachNewNode("StationContainer")
        self.station.setPos(0, 2500, 0)

        # Ana Kaide
        base_plate = GeoFactory.make_box(Vec3(35, 35, 2), Vec4(0.1, 0.1, 0.15, 1))
        base_plate.reparentTo(self.station);
        base_plate.setPos(0, 0, 1)

        # Enerji Odası (Merkez) - Çatı Yüksekliği: 12
        core_hub = GeoFactory.make_box(Vec3(15, 15, 12), Vec4(0.2, 0.25, 0.3, 1))
        core_hub.reparentTo(self.station);
        core_hub.setPos(0, 0, 6)

        # Parlayan Enerji Sütunları
        for pos_x, pos_y in [(-14, -14), (14, -14), (-14, 14), (14, 14)]:
            pillar = GeoFactory.make_box(Vec3(3, 3, 20), Vec4(0, 0.6, 1, 1))
            pillar.reparentTo(self.station);
            pillar.setPos(pos_x, pos_y, 10)

        # Dönen Enerji Çekirdeği (Radar)
        self.station_radar = GeoFactory.make_box(Vec3(12, 2, 2), Vec4(0, 1, 1, 1))
        self.station_radar.reparentTo(self.station);
        self.station_radar.setPos(0, 0, 18)

        # İstasyon Yazısı
        tn_st = TextNode('station_name');
        tn_st.setText("TEKO TEKNOLOJİ MERKEZİ\n(Geliştirme İçin Yaklaş)");
        tn_st.setTextColor(0, 1, 1, 1);
        tn_st.setAlign(TextNode.ACenter)
        st_p = self.station.attachNewNode(tn_st);
        st_p.setPos(0, 0, 25);
        st_p.setScale(3.0);
        st_p.setBillboardPointEye()

        self.decor = self.render.attachNewNode("decor")
        for _ in range(60):
            mx, my = random.uniform(-8000, 8000), random.uniform(200, 25000)
            m_h, m_w = random.uniform(300, 1000), random.uniform(500, 1200)
            m_col = Vec4(0.3 + random.random() * 0.1, 0.35, 0.3, 1)
            mountain = GeoFactory.make_mountain(m_h, m_w, m_col)
            mountain.reparentTo(self.decor);
            mountain.setPos(mx, my, -20)

        for _ in range(400):
            tx, ty = random.uniform(-3000, 3000), random.uniform(200, 15000)
            trunk = GeoFactory.make_box(Vec3(1.2, 1.2, 15), Vec4(0.3, 0.15, 0.05, 1))
            trunk.reparentTo(self.decor);
            trunk.setPos(tx, ty, 7.5)
            for i in range(3):
                leaf_col = Vec4(0.05, 0.3 + (i * 0.05), 0.05, 1)
                leaves = GeoFactory.make_tree_leaves(18 - (i * 4), leaf_col)
                leaves.reparentTo(self.decor);
                leaves.setPos(tx, ty, 12 + (i * 6))

        self.rings = []
        p_list = ["HIZ +", "BATARYA +", "+1500 PUAN"]
        for i in range(75):
            is_blue = random.random() < 0.3
            col = Vec4(0, 0.5, 1, 1) if is_blue else Vec4(1, 0.2, 0, 1)
            ring = GeoFactory.make_ring(r=8.0, col=col, seg=64)
            ring.reparentTo(self.render);
            ring.setPos(random.uniform(-500, 500), 500 + i * 180, random.uniform(25, 95))
            ring.setP(90)
            if is_blue:
                p_type = random.choice(p_list)
                ring.setPythonTag("p_type", p_type)
                tn_out = TextNode('blue_out');
                tn_out.setText("Teko Enerji");
                tn_out.setTextColor(0, 1, 1, 1);
                tn_out.setAlign(TextNode.ACenter)
                out_p = ring.attachNewNode(tn_out);
                out_p.setPos(0, 11, 0);
                out_p.setScale(1.1);
                out_p.setBillboardPointEye()
                tn_in = TextNode('blue_in');
                tn_in.setText(p_type);
                tn_in.setTextColor(1, 1, 1, 1);
                tn_in.setAlign(TextNode.ACenter)
                in_p = ring.attachNewNode(tn_in);
                in_p.setPos(0, 0, 0);
                in_p.setScale(0.9);
                in_p.setBillboardPointEye()
            else:
                ring.setPythonTag("p_type", "NONE")
                tn_red = TextNode('red_in');
                tn_red.setText("TEVFİK İLERİ");
                tn_red.setTextColor(1, 1, 0, 1);
                tn_red.setAlign(TextNode.ACenter)
                red_p = ring.attachNewNode(tn_red);
                red_p.setPos(0, 0, 0);
                red_p.setScale(0.9);
                red_p.setBillboardPointEye()
            self.rings.append(ring)

    def setup_drone(self):
        self.drone = self.render.attachNewNode("Drone")
        body = GeoFactory.make_box(Vec3(0.7, 1.9, 0.3), Vec4(0.1, 0.1, 0.1, 1))
        body.reparentTo(self.drone)
        cam = GeoFactory.make_box(Vec3(0.45, 0.35, 0.35), Vec4(0.05, 0.05, 0.05, 1))
        cam.reparentTo(self.drone);
        cam.setPos(0, 0.95, 0)
        self.props = []
        arm_positions = [(-1.1, 1.1), (1.1, 1.1), (-1.1, -1.1), (1.1, -1.1)]
        for i, (dx, dy) in enumerate(arm_positions):
            arm = GeoFactory.make_box(Vec3(0.25, 3.0, 0.12), Vec4(0.15, 0.15, 0.15, 1))
            arm.reparentTo(self.drone);
            arm.setH(45 if dx * dy > 0 else -45)
            motor = GeoFactory.make_box(Vec3(0.45, 0.45, 0.45), Vec4(0.25, 0.25, 0.25, 1))
            motor.reparentTo(self.drone);
            motor.setPos(dx * 1.3, dy * 1.3, 0.15)
            prop = GeoFactory.make_box(Vec3(1.5, 0.15, 0.05), Vec4(1, 1, 1, 0.5))
            prop.reparentTo(self.drone);
            prop.setPos(dx * 1.3, dy * 1.3, 0.45)
            self.props.append(prop)
        self.drone.hide()

    def setup_ui(self):
        self.ui_menu = self.aspect2d.attachNewNode("menu")
        OnscreenText("TEVFİK İLERİ AİHL", pos=(0, 0.6), scale=0.15, fg=(1, 1, 1, 1), parent=self.ui_menu,
                     shadow=(0, 0, 0, 1))
        OnscreenText("UFKA KANAT", pos=(0, 0.45), scale=0.1, fg=(1, 0.4, 0, 1), parent=self.ui_menu,
                     shadow=(0, 0, 0, 1))
        self.hs_text = OnscreenText(f"REKOR: {self.high_score}", pos=(0, 0.15), scale=0.08, fg=(1, 1, 0, 1),
                                    parent=self.ui_menu, shadow=(0, 0, 0, 1))
        OnscreenText("AHMET SAİD ADALAR  |  ÖMER PİLE  |  KEREM KARACA ", pos=(0, -0.05), scale=0.06,
                     fg=(0.9, 0.9, 0.9, 1), parent=self.ui_menu)
        OnscreenText("BAŞLAT: 'ENTER' | MAĞAZA: 'b'", pos=(0, -0.4), scale=0.07, fg=(1, 1, 1, 1), parent=self.ui_menu)
        self.shop_panel = self.aspect2d.attachNewNode("shop");
        self.shop_panel.hide()
        OnscreenText("--- TEKO MAĞAZA ---", pos=(0, 0.6), scale=0.1, fg=(0, 1, 1, 1), parent=self.shop_panel)
        self.sp_txt = OnscreenText("", pos=(0, 0.45), scale=0.07, fg=(1, 1, 1, 1), parent=self.shop_panel)
        OnscreenText("[1] MOTOR GÜCÜ (5000)\n[2] EKSTRA PİL (3000)\n[3] HASSAS DÖNÜŞ (4000)\n\n[b] ÇIKIŞ", pos=(0, 0),
                     scale=0.07, fg=(1, 1, 1, 1), parent=self.shop_panel)
        self.ui_hud = self.aspect2d.attachNewNode("hud");
        self.ui_hud.hide()
        self.skor_txt = OnscreenText("PUAN: 0", pos=(-1.25, 0.9), scale=0.08, fg=(1, 1, 1, 1), align=TextNode.ALeft,
                                     parent=self.ui_hud, shadow=(0, 0, 0, 1))
        self.bat_txt = OnscreenText("BATARYA: %100", pos=(-1.25, 0.8), scale=0.06, fg=(1, 1, 0, 1),
                                    align=TextNode.ALeft, parent=self.ui_hud, shadow=(0, 0, 0, 1))
        self.alt_txt = OnscreenText("İRTİFA: 0m", pos=(-1.25, 0.7), scale=0.06, fg=(0.8, 1, 0.8, 1),
                                    align=TextNode.ALeft, parent=self.ui_hud, shadow=(0, 0, 0, 1))

    def setup_audio(self):
        p = GeoFactory.create_sound_synthesis()
        self.engine_sfx = self.loader.loadSfx(Filename.from_os_specific(p))
        if self.engine_sfx: self.engine_sfx.setLoop(True); self.engine_sfx.setVolume(0)
        music_file = "muzik.wav"
        if os.path.exists(music_file):
            self.bg_music = self.loader.loadSfx(music_file)
            if self.bg_music: self.bg_music.setLoop(True); self.bg_music.setVolume(0.5)
        else:
            self.bg_music = None

    def setup_controls(self):
        for k in ["w", "s", "a", "d", "space", "lcontrol", "enter", "b", "1", "2", "3"]:
            self.accept(k, self.update_key, [k, True]);
            self.accept(k + "-up", self.update_key, [k, False])

    def update_key(self, k, v):
        self.keys[k] = v
        if k == "enter" and v and not self.is_playing and not self.is_shop_open: self.start_game()
        if k == "b" and v and not self.is_playing: self.toggle_shop()
        if self.is_shop_open and v:
            if k == "1": self.buy_upgrade("speed", 5000)
            if k == "2": self.buy_upgrade("battery", 3000)
            if k == "3": self.buy_upgrade("turn", 4000)

    def toggle_shop(self):
        self.is_shop_open = not self.is_shop_open
        if self.is_shop_open:
            self.shop_panel.show();
            self.ui_menu.hide();
            self.sp_txt.setText(f"PUANIN: {self.shop_points}")
        else:
            self.shop_panel.hide();
            if not self.is_playing: self.ui_menu.show()

    def buy_upgrade(self, type, cost):
        if self.shop_points >= cost:
            self.shop_points -= cost
            if type == "speed": self.up_speed += 0.35
            if type == "battery": self.up_battery += 0.35
            if type == "turn": self.up_turn += 0.25
            self.sp_txt.setText(f"GELİŞTİRİLDİ! KALAN: {self.shop_points}")

    def start_game(self):
        self.is_playing = True;
        self.points = 0;
        self.battery = 100.0 * self.up_battery
        self.pos, self.vel, self.hpr = Vec3(0, 0, 10), Vec3(0, 0, 0), Vec3(0, 0, 0)
        self.ui_menu.hide();
        self.ui_hud.show();
        self.drone.show()
        for r in self.rings: r.show()
        if self.engine_sfx: self.engine_sfx.play(); self.engine_sfx.setVolume(0.4)
        if self.bg_music: self.bg_music.play()

    def master_loop(self, task):
        dt = globalClock.getDt()

        # Nehir akıntısı animasyonu
        self.river.setTexOffset(TextureStage.getDefault(), 0, -task.time * 0.2)

        if self.is_playing:
            accel = Vec3(0, 0, 0)
            sp, tr = 75 * self.up_speed, 195 * self.up_turn
            if self.keys.get("w"): accel += self.drone.getQuat().xform(Vec3(0, sp, 0))
            if self.keys.get("s"): accel -= self.drone.getQuat().xform(Vec3(0, sp * 0.6, 0))
            if self.keys.get("a"): self.hpr.x += tr * dt
            if self.keys.get("d"): self.hpr.x -= tr * dt
            if self.keys.get("space"): accel.z += 55
            if self.keys.get("lcontrol"): accel.z -= 55

            # Fiziksel Hareket Hesaplama
            self.vel += (accel + Vec3(0, 0, -9.81) - self.vel * 1.8) * dt
            self.pos += self.vel * dt

            # --- İSTASYON ÇATI ÇARPIŞMASI (OTURMA MANTIĞI) ---
            stat_pos = self.station.getPos()
            # İstasyonun yatay alanı içindeyse (15x15'lik çekirdek)
            if abs(self.pos.x - stat_pos.x) < 8.0 and abs(self.pos.y - stat_pos.y) < 8.0:
                roof_z = stat_pos.z + 12.0  # Merkezin çatı yüksekliği
                if self.pos.z < roof_z:
                    self.pos.z = roof_z  # Merkezin içine girmeyi engelle (üstüne koy)
                    if self.vel.z < 0: self.vel.z = 0  # Düşme hızını sıfırla

            # Yer Çarpışması (Normal zemin)
            if self.pos.z < 0.5: self.game_over()

            self.drone.setPos(self.pos);
            self.drone.setHpr(self.hpr)
            for p in self.props: p.setH(p.getH() + 6000 * dt)

            self.battery -= dt * 0.65
            self.skor_txt.setText(f"PUAN: {self.points}")
            self.bat_txt.setText(f"BATARYA: %{int(self.battery)}")
            self.alt_txt.setText(f"İRTİFA: {int(self.pos.z)}m")

            self.station_radar.setH(self.station_radar.getH() + 150 * dt)

            # --- İSTASYON ETKİLEŞİMİ & MAĞAZA ---
            dist_to_station = (self.pos - self.station.getPos()).length()
            if dist_to_station < 25:
                self.battery = 100.0 * self.up_battery
                if not self.is_shop_open: self.toggle_shop()
            elif self.is_shop_open:
                self.toggle_shop()  # İstasyondan uzaklaşınca mağaza kapanır

            for r in self.rings:
                if not r.isHidden() and (r.getPos() - self.pos).length() < 9.0:
                    r.hide()
                    p_type = r.getPythonTag("p_type")
                    if p_type == "NONE":
                        self.points += 1000
                    else:
                        self.points += 500
                        if p_type == "BATARYA +":
                            self.battery = min(100 * self.up_battery, self.battery + 25)
                        elif p_type == "HIZ +":
                            self.up_speed += 0.05
                        elif p_type == "+ PUAN":
                            self.points += 1000
            tp = self.pos + self.drone.getQuat().xform(Vec3(0, -25, 12))
            self.camera.setPos(self.camera.getPos() + (tp - self.camera.getPos()) * 7.0 * dt)
            self.camera.lookAt(self.pos + Vec3(0, 15, 0))
            if self.battery <= 0: self.game_over()
        else:
            self.camera.setPos(300 * cos(task.time * 0.1), 300 * sin(task.time * 0.1), 150)
            self.camera.lookAt(0, 0, 0)
        return task.cont

    def game_over(self):
        if self.points > self.high_score:
            self.high_score = self.points
            with open("highscore.txt", "w") as f: f.write(str(self.high_score))
        self.shop_points += self.points
        self.is_playing = False;
        self.ui_menu.show();
        self.ui_hud.hide();
        self.drone.hide()
        self.hs_text.setText(f"REKOR: {self.high_score}")
        if self.engine_sfx: self.engine_sfx.stop()
        if self.bg_music: self.bg_music.stop()


if __name__ == "__main__":
    app = UfkaKanatV5()
    app.run()