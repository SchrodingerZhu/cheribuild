#
# SPDX-License-Identifier: BSD-2-Clause
#
# Copyright (c) 2020 Alex Richardson
#
# This work was supported by Innovate UK project 105694, "Digital Security by
# Design (DSbD) Technology Platform Prototype".
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR AND CONTRIBUTORS ``AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED.  IN NO EVENT SHALL THE AUTHOR OR CONTRIBUTORS BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
from .crosscompileproject import CrossCompileAutotoolsProject, CrossCompileCMakeProject, CrossCompileMesonProject
from ..project import DefaultInstallDir, GitRepository
from ...config.chericonfig import CheriConfig
from ...config.compilation_targets import CompilationTargets


class BuildEPollShim(CrossCompileCMakeProject):
    target = "epoll-shim"
    project_name = "epoll-shim"
    native_install_dir = DefaultInstallDir.IN_BUILD_DIRECTORY
    cross_install_dir = DefaultInstallDir.ROOTFS_LOCALBASE
    repository = GitRepository("https://github.com/jiixyj/epoll-shim")
    # TODO: could build it native on FreeBSD as well
    supported_architectures = CompilationTargets.ALL_FREEBSD_AND_CHERIBSD_TARGETS

    def configure(self, **kwargs):
        if not self.compiling_for_host():
            # external/microatf/cmake/ATFTestAddTests.cmake breaks cross-compilation
            self.add_cmake_options(BUILD_TESTING=False)
        super().configure()


class BuildExpat(CrossCompileCMakeProject):
    target = "libexpat"
    project_name = "libexpat"
    native_install_dir = DefaultInstallDir.IN_BUILD_DIRECTORY
    cross_install_dir = DefaultInstallDir.ROOTFS_LOCALBASE
    repository = GitRepository("https://github.com/libexpat/libexpat")
    supported_architectures = CompilationTargets.ALL_FREEBSD_AND_CHERIBSD_TARGETS + [CompilationTargets.NATIVE]

    def configure(self, **kwargs):
        if not self.compiling_for_host():
            # Work around CMAKE_CXX_FLAGS being overwritten (https://github.com/libexpat/libexpat/pull/442)
            self.add_cmake_options(EXPAT_BUILD_TESTS=False)
        # The actual source is in a subdirectory, so update configure_args
        self.configure_args[0] = str(self.source_dir / "expat")
        super().configure(**kwargs)


class BuildLibFFI(CrossCompileAutotoolsProject):
    repository = GitRepository("https://github.com/libffi/libffi.git")
    project_name = "libffi"
    native_install_dir = DefaultInstallDir.IN_BUILD_DIRECTORY
    cross_install_dir = DefaultInstallDir.ROOTFS_LOCALBASE
    supported_architectures = CompilationTargets.ALL_FREEBSD_AND_CHERIBSD_TARGETS + [CompilationTargets.NATIVE]

    def configure(self, **kwargs):
        self.run_cmd(self.source_dir / "autogen.sh", cwd=self.source_dir)
        super().configure(**kwargs)


class BuildWayland(CrossCompileMesonProject):
    @classmethod
    def dependencies(cls, config: CheriConfig):
        deps = super().dependencies(config)
        target = cls.get_crosscompile_target(config)
        if not target.is_native():
            # For native builds we use the host libraries
            deps.extend(["libexpat", "libffi", "libxml2"])
            # We need a native wayland-scanner during the build
            deps.append("wayland-native")
        if target.target_info_cls.is_freebsd():
            deps += ["epoll-shim"]
        return deps

    native_install_dir = DefaultInstallDir.BOOTSTRAP_TOOLS
    cross_install_dir = DefaultInstallDir.ROOTFS_LOCALBASE
    # TODO: upstream patches and use https://gitlab.freedesktop.org/wayland/wayland.git
    repository = GitRepository("https://github.com/CTSRD-CHERI/wayland")
    supported_architectures = CompilationTargets.ALL_FREEBSD_AND_CHERIBSD_TARGETS + [CompilationTargets.NATIVE]

    def setup(self):
        super().setup()
        # Can be set to False to avoid libxml2 depdency:
        self.add_meson_options(dtd_validation=True)
        # Avoid docbook depedency
        self.add_meson_options(documentation=False)
        if self.target_info.is_macos():
            # Only build wayland-scanner
            self.add_meson_options(libraries=False)
