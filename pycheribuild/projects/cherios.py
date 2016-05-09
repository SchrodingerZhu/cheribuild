import os
import re

from ..project import Project
from ..utils import *


class BuildCheriOS(Project):
    def __init__(self, config: CheriConfig):
        super().__init__(config, installDir=config.outputRoot / ("cherios" + config.cheriBitsStr),
                         gitUrl="https://github.com/CTSRD-CHERI/cherios.git", appendCheriBitsToBuildDir=True)
        self.makeCommand = "ninja"
        self.configureCommand = "cmake"
        self._addRequiredSystemTool("cmake", installInstructions=self.cmakeInstallInstructions)
        self.configureArgs.extend([
            self.sourceDir, "-G", "Ninja", "-DCMAKE_BUILD_TYPE=Debug",
            "-DCMAKE_INSTALL_PREFIX=" + str(self.installDir),
            "-DCHERI_SDK_DIR=" + str(self.config.sdkDir),
        ])

    def checkSystemDependencies(self):
        super().checkSystemDependencies()
        # try to find cmake 3.4 or newer
        versionPattern = re.compile(b"cmake version (\\d+)\\.(\\d+)\\.?(\\d+)?")
        # cmake prints this output to stdout
        versionString = runCmd("cmake", "--version", captureOutput=True, printVerboseOnly=True).stdout
        match = versionPattern.search(versionString)
        versionComponents = tuple(map(int, match.groups())) if match else (0, 0, 0)
        if versionComponents < (3, 5):
            versionStr = ".".join(map(str, versionComponents))
            self.dependencyError("CMake version", versionStr, "is too old (need at least 3.4)",
                                 installInstructions=self.cmakeInstallInstructions)

    def install(self):
        pass  # nothing to install yet
